"""
revenue_forecast.py — Main orchestration entry point for TrustAgri AI.

Exposes run_forecast(state, district, crop_list) as a callable function so it
can be invoked directly by a REST API, mobile backend, or another Python module
without blocking on stdin input().

Pipeline:
  1. Fetch current weather (temperature, humidity) from OpenWeatherMap.
  2. Fetch annual rainfall (mm/year) from Open-Meteo Historical Archive.
  3. Build weather_inputs dict for the ML model.
  4. Run crop recommendation engine (yield × price / supply).
  5. Append risk analysis to each recommendation.
  6. Return a fully JSON-serializable result dict.
"""

import datetime

from ai_modules.yield_prediction.weather_service          import fetch_weather_data
from ai_modules.yield_prediction.crop_recommendation_engine import recommend_crops
from ai_modules.yield_prediction.risk_analysis            import analyze_risk
from ai_modules.yield_prediction.config import (
    DEFAULT_CROP_LIST,
    DEFAULT_WEATHER,
)


def run_forecast(
    state: str,
    district: str,
    crop_list: list[str] | None = None,
) -> dict:
    """
    Run the full TrustAgri crop recommendation pipeline for a given region.

    Args:
        state      (str):         State name (e.g. "Tamil Nadu").
        district   (str):         District name (e.g. "Thanjavur").
        crop_list  (list | None): Crops to evaluate. Defaults to DEFAULT_CROP_LIST.

    Returns:
        dict: Fully JSON-serializable result containing:
              - state, district
              - weather (temperature, humidity, rainfall_mm, rainfall_source)
              - crop_list_evaluated
              - recommended_crops (top 3 with yield, price, supply, risk)
    """
    if crop_list is None:
        crop_list = DEFAULT_CROP_LIST

    # --- Step 1 & 2: Fetch weather + annual rainfall ---
    weather_data  = fetch_weather_data(district)
    weather_api_ok = "error" not in weather_data

    if not weather_api_ok:
        temperature      = DEFAULT_WEATHER["temperature"]
        rainfall         = DEFAULT_WEATHER["rainfall"]
        humidity         = DEFAULT_WEATHER["humidity"]
        rainfall_source  = "default_fallback"
    else:
        temperature = weather_data.get("temperature",  DEFAULT_WEATHER["temperature"])
        humidity    = weather_data.get("humidity",     DEFAULT_WEATHER["humidity"])

        # rainfall is annual mm/year from Open-Meteo; None means API failed
        raw_rain   = weather_data.get("rainfall")
        rainfall   = raw_rain if (raw_rain is not None and raw_rain > 0) else DEFAULT_WEATHER["rainfall"]
        rainfall_source = weather_data.get("rainfall_source", "default_fallback")

    # --- Step 3: Build ML model input ---
    weather_inputs = {
        "year":        datetime.datetime.now().year,
        "rainfall":    rainfall,          # annual mm/year — matches training scale
        "temperature": temperature,
        "pesticides":  DEFAULT_WEATHER["pesticides"],
    }

    # --- Step 4: Run recommendation engine ---
    recommendations = recommend_crops(state, district, crop_list, weather_inputs)

    # --- Step 5: Append risk analysis to each recommendation ---
    for rec in recommendations:
        risk = analyze_risk(temperature, rainfall, rec["market_price"])
        rec["risk_level"]  = risk["risk_level"]
        rec["risk_reason"] = risk["reason"]

    return {
        "state":    state,
        "district": district,
        "weather": {
            "temperature":    temperature,
            "humidity":       humidity,
            "rainfall_mm":    rainfall,
            "rainfall_source": rainfall_source,
            "weather_api_ok": weather_api_ok,
        },
        "crop_list_evaluated": crop_list,
        "recommended_crops":   recommendations,
    }


if __name__ == "__main__":
    import json
    result = run_forecast("Tamil Nadu", "Thanjavur")
    print(json.dumps(result, indent=2))
