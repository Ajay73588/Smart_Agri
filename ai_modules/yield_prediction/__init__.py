"""
TrustAgri AI — yield_prediction package

Exposes the top-level public API for import by teammates and backend services.

Usage:
    from ai_modules.yield_prediction import run_forecast, recommend_crops
"""

from ai_modules.yield_prediction.revenue_forecast          import run_forecast
from ai_modules.yield_prediction.crop_recommendation_engine import recommend_crops
from ai_modules.yield_prediction.weather_service           import fetch_weather_data
from ai_modules.yield_prediction.risk_analysis             import analyze_risk
from ai_modules.yield_prediction.supply_analysis           import get_supply_index, get_region_crop_supply
from ai_modules.yield_prediction.agmarknet_price_service   import fetch_crop_price
from ai_modules.yield_prediction.predict_model             import predict_crop_yield, get_supported_crops

__all__ = [
    "run_forecast",
    "recommend_crops",
    "fetch_weather_data",
    "analyze_risk",
    "get_supply_index",
    "get_region_crop_supply",
    "fetch_crop_price",
    "predict_crop_yield",
    "get_supported_crops",
]
