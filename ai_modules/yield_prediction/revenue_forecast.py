"""
revenue_forecast.py — Main orchestration entry point for TrustAgri AI.

Exposes run_forecast(state, district) as a pure callable function so it can be
invoked directly by a REST API, mobile backend, or another Python module without
blocking on stdin input().
"""
import datetime

from weather_service import fetch_weather_data
from crop_recommendation_engine import recommend_crops
from risk_analysis import analyze_risk
from config import DEFAULT_CROP_LIST, DEFAULT_WEATHER

def run_forecast(state, district, crop_list=None):
    """
    Run the full TrustAgri crop recommendation pipeline for a given region.

    Args:
        state (str): State name (e.g. "Tamil Nadu").
        district (str): District name (e.g. "Thanjavur").
        crop_list (list, optional): Crops to evaluate. Defaults to DEFAULT_CROP_LIST.

    Returns:
        dict: Fully JSON-serializable result containing weather, recommended crops,
              and risk levels. Safe to return directly from a FastAPI endpoint.
    """
    if crop_list is None:
        crop_list = DEFAULT_CROP_LIST

    # --- Step 1: Fetch weather data ---
    weather_data = fetch_weather_data(district)
    weather_api_ok = "error" not in weather_data

    if not weather_api_ok:
        temperature = DEFAULT_WEATHER["temperature"]
        rainfall = DEFAULT_WEATHER["rainfall"]
        humidity = DEFAULT_WEATHER["humidity"]
    else:
        temperature = weather_data.get("temperature", DEFAULT_WEATHER["temperature"])
        raw_rain = weather_data.get("rainfall", 0.0)
        # If rainfall estimate is 0 (no active rain), fall back to safe default
        rainfall = raw_rain if raw_rain > 0 else DEFAULT_WEATHER["rainfall"]
        humidity = weather_data.get("humidity", DEFAULT_WEATHER["humidity"])

    # --- Step 2: Build weather inputs for the ML model ---
    weather_inputs = {
        "year": datetime.datetime.now().year,
        "rainfall": rainfall,
        "temperature": temperature,
        "pesticides": DEFAULT_WEATHER["pesticides"]
    }

    # --- Step 3: Run recommendation engine (handles yield, price, supply internally) ---
    recommendations = recommend_crops(state, district, crop_list, weather_inputs)

    # --- Step 4: Append risk analysis to each recommendation ---
    for rec in recommendations:
        risk = analyze_risk(temperature, rainfall, rec["market_price"])
        rec["risk_level"] = risk["risk_level"]
        rec["risk_reason"] = risk["reason"]

    return {
        "state": state,
        "district": district,
        "weather": {
            "temperature": temperature,
            "rainfall_mm": rainfall,
            "humidity": humidity,
            "weather_api_ok": weather_api_ok
        },
        "crop_list_evaluated": crop_list,
        "recommended_crops": recommendations
    }

if __name__ == "__main__":
    # Terminal demo — uses defaults, no input() needed
    import json
    result = run_forecast("Tamil Nadu", "Thanjavur")
    print(json.dumps(result, indent=2))
