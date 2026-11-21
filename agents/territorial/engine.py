"""Sobreposição espacial conservadora de zonas, ruas, setores e equipamentos.

NÃO é modelo hidráulico e NÃO autoriza alerta público.
- A cota de disparo em cm deve estar calibrada para a MESMA estação/régua.
- O 'tempo' é quando a previsão cruza um limiar da régua, não a chegada da água à rua.
- População usa interpolação areal uniforme; é estimativa agregada aproximada.
"""
from __future__ import annotations

import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

from .models import ForecastRequest, TerritorialReport, ExposedZone

_DEMO = Path(__file__).resolve().parent / "demo_data"
_PROJECTION = Transformer.from_crs("EPSG:4326", "EPSG:5880", always_xy=True).transform


def _load_geojson(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if obj.get("type") != "FeatureCollection":
        raise ValueError(f"GeoJSON inválido: {path}")
    return obj.get("features", [])


def load_catalog(folder: str | Path = _DEMO) -> dict[str, list[dict]]:
    base = Path(folder)
    return {key: _load_geojson(base / f"{key}.geojson") for key in ("zones", "sectors", "streets", "facilities")}


def _crossing_minutes(points, threshold):
    """Primeiro cruzamento crescente do limiar; não estima propagação de inundação."""
    if points[0].level_cm >= threshold:
        return 0.0
    for before, after in zip(points, points[1:]):
        if before.level_cm < threshold <= after.level_cm:
            delta = after.level_cm - before.level_cm
            if delta <= 0:
                return None
            fraction = (threshold - before.level_cm) / delta
            return round(before.horizon_minutes + fraction * (after.horizon_minutes - before.horizon_minutes), 1)
    return None


def _weighted_population(geom, census_sectors):
    """Interpolação por área em CRS de área equivalente. Hipótese uniforme por setor."""
    total = 0.0
    projected_zone = transform(_PROJECTION, geom)
    for item in census_sectors:
        sector_geom = transform(_PROJECTION, shape(item["geometry"]))
        if sector_geom.is_empty or sector_geom.area <= 0:
            continue
        overlap = projected_zone.intersection(sector_geom)
        if not overlap.is_empty:
            amount = int(item.get("properties", {}).get("population", 0))
            total += amount * overlap.area / sector_geom.area
    return max(0, round(total))


def analyze_territorial_impact(
    forecast: ForecastRequest,
    catalog: dict[str, list[dict]],
) -> TerritorialReport:
    """Interpreta apenas zonas previamente cadastradas e vinculadas à estação.

    Fail-closed: nunca mistura catálogo de demonstração com previsões reais.
    """
    allzones = catalog["zones"]
    applicable = []
    for feature in allzones:
        props = feature["properties"]
        if props.get("station_id") == forecast.station_id:
            applicable.append(feature)
    if not applicable:
        raise ValueError("Sem áreas geográficas cadastradas para esta estação")
    for z in applicable:
        p = z["properties"]
        if p.get("mapping_method") not in ("demonstration_threshold", "approved_calibrated"):
            raise ValueError("Zonas precisam indicar o método que vincula régua e área")
        if forecast.environment == "real" and p.get("mapping_method") != "approved_calibrated":
            raise ValueError("Catálogo de demonstração não pode processar previsões de produção")
        if "threshold_level_cm" not in p:
            raise ValueError("Zona sem limiar referenciado à estação")
        if not shape(z["geometry"]).is_valid:
            raise ValueError("Geometria de zona inválida")

    results = []
    impacted_geoms = []
    for f in applicable:
        props = f["properties"]
        crossed = _crossing_minutes(forecast.points, float(props["threshold_level_cm"]))
        if crossed is None:
            continue
        geom = shape(f["geometry"])
        impacted_geoms.append(geom)
        streets = sorted(set(str(r["properties"].get("name", "Trecho sem identificação"))
                             for r in catalog["streets"] if geom.intersection(shape(r["geometry"])).length > 0))
        facilities = sorted(set(str(p["properties"].get("name", "Equipamento sem identificação"))
                                for p in catalog["facilities"] if geom.intersects(shape(p["geometry"]))))
        results.append(ExposedZone(
            zone_id=str(props["zone_id"]), neighborhood=str(props["neighborhood"]),
            risk_class=str(props.get("risk_class", "not_evaluated")),
            threshold_level_cm=float(props["threshold_level_cm"]),
            crossing_time_minutes=crossed,
            population_estimate=_weighted_population(geom, catalog["sectors"]),
            streets=streets, critical_facilities=facilities,
            mapping_source=str(props.get("mapping_source", "não informado")),
        ))
    results.sort(key=lambda x: (x.crossing_time_minutes, x.zone_id))
    unique_population = _weighted_population(unary_union(impacted_geoms), catalog["sectors"]) if impacted_geoms else 0
    return TerritorialReport(
        event_id=forecast.event_id, station_id=forecast.station_id,
        environment=forecast.environment, assessed_at=forecast.issued_at,
        classification="potential_exposure" if results else "no_mapped_exposure",
        affected_zones=results, total_population_estimate=unique_population,
        impacted_streets=sorted(set(s for zone in results for s in zone.streets)),
        critical_facilities=sorted(set(s for zone in results for s in zone.critical_facilities)),
        data_sources=sorted(set(str(z["properties"].get("mapping_source", "não informado")) for z in applicable)),
        limitations=[
            "RESULTADO EXPERIMENTAL; não usar para decisões de evacuação ou alertas públicos.",
            "Cruzamento de limiar de uma estação NÃO equivale ao horário de chegada da água em uma rua.",
            "As zonas são pré-mapeadas; a saída NÃO estima a mancha hidráulica real de inundação.",
            "População proporcional à área do setor assume distribuição uniforme; apenas valor agregado aproximado.",
            "Comparações de altimetria só são válidas com datum vertical, estação e referenciais compatíveis.",
        ],
    )
