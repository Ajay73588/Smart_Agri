"""
TrustAgri FastAPI layer — api/main.py

Exposes the AI recommendation engine as a REST API.

Run from the project root with:
    uvicorn api.main:app --reload

Endpoints:
    GET  /                    — health check
    POST /recommend-crops     — full crop recommendation pipeline
    POST /weather             — real-time weather + annual rainfall
    POST /supply              — supply index for all crops in a region
    GET  /supported-crops     — list of crops the ML model supports
"""

import sys
import os

# Ensure project root is on sys.path for absolute package imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from ai_modules.yield_prediction.revenue_forecast        import run_forecast
from ai_modules.yield_prediction.weather_service         import fetch_weather_data
from ai_modules.yield_prediction.supply_analysis         import get_region_crop_supply
from ai_modules.yield_prediction.predict_model           import get_supported_crops

app = FastAPI(
    title="TrustAgri AI API",
    description=(
        "AI-powered crop recommendation engine for smart farming decisions. "
        "Uses a RandomForest ML model, live Agmarknet prices, and Open-Meteo "
        "annual rainfall data to recommend the top 3 crops for any Indian region."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response Models ---

class RecommendRequest(BaseModel):
    state:     str
    district:  str
    crop_list: Optional[List[str]] = None  # Defaults to config.DEFAULT_CROP_LIST


class WeatherRequest(BaseModel):
    district: str


class SupplyRequest(BaseModel):
    state:    str
    district: str


# --- Endpoints ---

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "TrustAgri AI API", "version": "1.1.0"}


@app.get("/supported-crops", tags=["Meta"])
def list_supported_crops():
    """Return the list of crop names the ML model was trained on."""
    crops = get_supported_crops()
    return {"count": len(crops), "crops": sorted(crops)}


@app.post("/recommend-crops", tags=["Recommendations"])
def recommend_crops_endpoint(request: RecommendRequest):
    """
    Run the full TrustAgri pipeline and return crop recommendations.

    Input:  {"state": "Tamil Nadu", "district": "Thanjavur"}
    Output: {state, district, weather, crop_list_evaluated, recommended_crops}
    """
    result = run_forecast(
        state=request.state,
        district=request.district,
        crop_list=request.crop_list,
    )
    if not result.get("recommended_crops"):
        raise HTTPException(
            status_code=404,
            detail="No crop recommendations found for this region.",
        )
    return result


@app.post("/weather", tags=["Weather"])
def get_weather(request: WeatherRequest):
    """
    Fetch real-time temperature, humidity, and annual rainfall estimate for a district.

    Annual rainfall is sourced from Open-Meteo Historical Archive (last 365 days).
    This value is the same scale used by the ML model for predictions.
    """
    data = fetch_weather_data(request.district)
    if "error" in data:
        raise HTTPException(status_code=503, detail=data["error"])
    return data


@app.post("/supply", tags=["Supply"])
def get_supply(request: SupplyRequest):
    """Return supply index for all crops grown in a given region."""
    data = get_region_crop_supply(request.state, request.district)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No supply data found for this region.",
        )
    return {
        "state":      request.state,
        "district":   request.district,
        "supply_map": data,
    }
