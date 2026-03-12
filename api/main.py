"""
TrustAgri FastAPI layer — api/main.py

Exposes the AI recommendation engine as a REST API.

Run with:
    uvicorn api.main:app --reload

Then POST to: http://localhost:8000/recommend-crops
"""
import sys
import os

# Add the project root to sys.path so ai_modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from ai_modules.yield_prediction.revenue_forecast import run_forecast
from ai_modules.yield_prediction.weather_service import fetch_weather_data
from ai_modules.yield_prediction.supply_analysis import get_region_crop_supply

app = FastAPI(
    title="TrustAgri AI API",
    description="AI-powered crop recommendation engine for smart farming decisions.",
    version="1.0.0"
)

# Allow frontend / mobile app to call this API from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Request / Response Models ---

class RecommendRequest(BaseModel):
    state: str
    district: str
    crop_list: Optional[List[str]] = None  # Optional override; defaults to config.DEFAULT_CROP_LIST

class WeatherRequest(BaseModel):
    district: str

class SupplyRequest(BaseModel):
    state: str
    district: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "ok", "service": "TrustAgri AI API"}

@app.post("/recommend-crops")
def recommend_crops_endpoint(request: RecommendRequest):
    """
    Run the full TrustAgri pipeline and return crop recommendations.

    Input:  {"state": "Tamil Nadu", "district": "Thanjavur"}
    Output: {"state", "district", "weather", "recommended_crops": [...]}
    """
    result = run_forecast(
        state=request.state,
        district=request.district,
        crop_list=request.crop_list
    )
    if not result.get("recommended_crops"):
        raise HTTPException(status_code=404, detail="No crop recommendations found for this region.")
    return result

@app.post("/weather")
def get_weather(request: WeatherRequest):
    """Fetch real-time weather data for a district."""
    data = fetch_weather_data(request.district)
    if "error" in data:
        raise HTTPException(status_code=503, detail=data["error"])
    return data

@app.post("/supply")
def get_supply(request: SupplyRequest):
    """Return supply index for all crops in a given region."""
    data = get_region_crop_supply(request.state, request.district)
    if not data:
        raise HTTPException(status_code=404, detail="No supply data found for this region.")
    return {"state": request.state, "district": request.district, "supply_map": data}
