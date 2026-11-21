from copy import deepcopy
from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

from agents.territorial.api import app
from agents.territorial import load_catalog, analyze_territorial_impact, ForecastRequest

BASE = Path(__file__).resolve().parents[1]


def payload():
    return json.loads((BASE / "forecast_demo.json").read_text(encoding="utf-8"))


def test_areas_sorted_and_population_aggregated():
    report = analyze_territorial_impact(ForecastRequest.model_validate(payload()), load_catalog())
    assert [x.zone_id for x in report.affected_zones] == ["DEMO-01", "DEMO-02"]
    assert report.affected_zones[0].crossing_time_minutes == 50.0
    assert report.affected_zones[1].crossing_time_minutes > 100
    assert report.total_population_estimate > 0
    assert len(report.impacted_streets) == 2
    assert len(report.critical_facilities) == 2
    assert not report.external_public_alert_permitted
    assert not report.physical_water_arrival_time_available


def test_no_zone_crossed():
    p = payload()
    for x in p["points"]:
        x["level_cm"] = 80
    report = analyze_territorial_impact(ForecastRequest.model_validate(p), load_catalog())
    assert report.classification == "no_mapped_exposure"
    assert report.total_population_estimate == 0


def test_bad_station_fails_closed():
    p = payload()
    p["station_id"] = "DESCONHECIDA"
    with pytest.raises(ValueError, match="Sem áreas"):
        analyze_territorial_impact(ForecastRequest.model_validate(p), load_catalog())


def test_demo_zones_cannot_run_with_real_data():
    p = payload()
    p["environment"] = "real"
    with pytest.raises(ValueError, match="demonstração"):
        analyze_territorial_impact(ForecastRequest.model_validate(p), load_catalog())


def test_invalid_sequence_fails():
    p = payload()
    p["points"][1]["horizon_minutes"] = 0
    with pytest.raises(ValueError):
        ForecastRequest.model_validate(p)


def test_endpoint_success_and_rejects_real():
    client = TestClient(app)
    assert client.post("/territorial/analyze", json=payload()).status_code == 200
    p = payload()
    p["environment"] = "real"
    assert client.post("/territorial/analyze", json=p).status_code == 422


def test_overlapping_zones_are_not_double_counted():
    catalog = load_catalog()
    duplicate_zone = deepcopy(catalog["zones"][0])
    duplicate_zone["properties"]["zone_id"] = "DEMO-CLONE"
    catalog["zones"].append(duplicate_zone)
    r = analyze_territorial_impact(ForecastRequest.model_validate(payload()), catalog)
    baseline = analyze_territorial_impact(ForecastRequest.model_validate(payload()), load_catalog())
    assert r.total_population_estimate == baseline.total_population_estimate
