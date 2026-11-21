"""Contratos entre Agente #5, Agente #6 e orquestrador.

Versão 0.1: estes contratos DEVEM ser alinhados com a equipe antes da integração.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ForecastPoint(BaseModel):
    horizon_minutes: int = Field(ge=0, le=360)
    level_cm: float = Field(ge=0, le=100000)
    overflow_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    low_level_cm: float | None = Field(default=None, ge=0)
    high_level_cm: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_interval(self):
        if self.low_level_cm is not None and self.high_level_cm is not None:
            if self.low_level_cm > self.high_level_cm:
                raise ValueError("low_level_cm não pode exceder high_level_cm")
        return self


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=3)
    station_id: str = Field(min_length=3)
    issued_at: datetime
    environment: Literal["simulation", "real"] = "simulation"
    measurement_reference: Literal["relative_sensor_cm"] = "relative_sensor_cm"
    points: list[ForecastPoint] = Field(min_length=2)

    @model_validator(mode="after")
    def check_series(self):
        times = [p.horizon_minutes for p in self.points]
        if times != sorted(set(times)) or times[0] != 0:
            raise ValueError("Horizontes devem ser únicos, ordenados e iniciar em 0")
        if self.issued_at.tzinfo is None or self.issued_at.utcoffset() is None:
            raise ValueError("issued_at deve conter fuso horário")
        return self


class ExposedZone(BaseModel):
    zone_id: str
    neighborhood: str
    risk_class: str
    threshold_level_cm: float
    crossing_time_minutes: float
    population_estimate: int
    streets: list[str]
    critical_facilities: list[str]
    mapping_source: str
    estimate_type: Literal["proxy_sensor_threshold"] = "proxy_sensor_threshold"


class TerritorialReport(BaseModel):
    event_id: str
    station_id: str
    environment: Literal["simulation", "real"]
    assessed_at: datetime
    classification: Literal["potential_exposure", "no_mapped_exposure"]
    affected_zones: list[ExposedZone]
    total_population_estimate: int
    impacted_streets: list[str]
    critical_facilities: list[str]
    is_hydraulic_flood_extent: bool = False
    physical_water_arrival_time_available: bool = False
    external_public_alert_permitted: bool = False
    data_sources: list[str]
    limitations: list[str]
