"""API experimental para orquestrador chamar o Agente #6."""
from fastapi import FastAPI, HTTPException
from .engine import analyze_territorial_impact, load_catalog
from .models import ForecastRequest, TerritorialReport

app = FastAPI(title="Agente de Impacto Territorial — demonstração", version="0.1.0")
CATALOG = load_catalog()


@app.get("/health")
def health():
    return {"status": "ok", "component": "territorial", "environment": "simulation"}


@app.post("/territorial/analyze", response_model=TerritorialReport)
def analyze(forecast: ForecastRequest):
    try:
        return analyze_territorial_impact(forecast, CATALOG)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
