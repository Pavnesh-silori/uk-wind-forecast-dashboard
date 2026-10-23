from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.elexon_client import (
    fetch_actual_generation,
    fetch_forecast_generation,
)
from app.services.forecast_analysis import analyse_forecasts

app = FastAPI(
    title="UK Wind Forecast Dashboard API",
    description="Compare actual UK wind generation with forecasts from Elexon.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "UK Wind Forecast Dashboard API is running"
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/analysis")
def get_analysis():
    """
    Analyse January 2026 wind generation.
    The provisional purchasing cutoff is 10:00 UTC on the day
    before each delivery date.
    """

    try:
        # Actual-generation settlement dates are inclusive.
        actual_records = fetch_actual_generation(
            date(2026, 1, 1),
            date(2026, 1, 31),
        )

        # Retrieve forecasts published during December and January.
        # December data may be needed for early January deliveries.
        forecast_records = fetch_forecast_generation(
            date(2025, 12, 1),
            date(2026, 2, 1),
        )

        result = analyse_forecasts(
            actual_records,
            forecast_records,
            cutoff_hour_utc=10,
        )

        result["period"] = {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        }

        result["data_sources"] = {
            "actual": "Elexon BMRS FUELHH",
            "forecast": "Elexon BMRS WINDFOR",
        }

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve or analyse Elexon data: {exc}",
        ) from exc