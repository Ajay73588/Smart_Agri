"""
TrustAgri AI — yield_prediction package

Exposes the top-level public API for import by teammates and backend services.

Usage:
    from ai_modules.yield_prediction import run_forecast, recommend_crops
"""
from .revenue_forecast import run_forecast
from .crop_recommendation_engine import recommend_crops
from .weather_service import fetch_weather_data
from .risk_analysis import analyze_risk
from .supply_analysis import get_supply_index, get_region_crop_supply
from .agmarknet_price_service import fetch_crop_price

__all__ = [
    "run_forecast",
    "recommend_crops",
    "fetch_weather_data",
    "analyze_risk",
    "get_supply_index",
    "get_region_crop_supply",
    "fetch_crop_price"
]
