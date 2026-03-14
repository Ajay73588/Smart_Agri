"""
weather_service.py — Real-time weather and annual rainfall fetching.

This module provides two things:
  1. fetch_weather_data(city_name) — real-time temperature and humidity
     sourced from the OpenWeatherMap Current Weather API.
  2. fetch_annual_rainfall(lat, lon) — last-12-month total precipitation (mm)
     sourced from the Open-Meteo Historical Weather API (free, no API key).

IMPORTANT — Rainfall Unit Convention
--------------------------------------
The ML model (yield_model.pkl) was trained on the FAO crop yield dataset which
uses ANNUAL rainfall totals in mm/year (typical range: 200–3000 mm).

The OpenWeatherMap API returns 1-hour rainfall, which is useless for this
purpose (0.0 on any dry day, and never reaches annual scale).

Instead, annual rainfall is fetched from Open-Meteo:
  https://archive-api.open-meteo.com/v1/archive
  Endpoint returns daily precipitation_sum for any date range.
  We sum the last 365 days → annual_rainfall_mm.

This value is passed directly to the ML model as
`average_rain_fall_mm_per_year`, matching the training feature exactly.
"""

import os
import datetime
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# OpenWeatherMap — used only for temperature + humidity (NOT rainfall)
# ---------------------------------------------------------------------------
_OW_API_KEY = os.getenv("OPENWEATHER_API_KEY")
_OW_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# ---------------------------------------------------------------------------
# Open-Meteo Geocoding — converts city/district name → lat/lon
# ---------------------------------------------------------------------------
_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# ---------------------------------------------------------------------------
# Open-Meteo Historical Archive — annual precipitation (free, no key)
# ---------------------------------------------------------------------------
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _geocode(city_name: str) -> tuple[float, float] | None:
    """
    Return (latitude, longitude) for a city or district name using the
    Open-Meteo geocoding API.  Returns None if the city is not found.
    """
    try:
        resp = requests.get(
            _GEOCODING_URL,
            params={"name": city_name, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["latitude"], results[0]["longitude"]
    except requests.exceptions.RequestException:
        pass
    return None


def fetch_annual_rainfall(lat: float, lon: float) -> float | None:
    """
    Fetch the total precipitation (mm) over the last 12 months for a
    geographic coordinate using the Open-Meteo Historical Archive API.

    Unit returned: mm/year (annual total).
    This directly matches the 'average_rain_fall_mm_per_year' feature the ML
    model was trained on.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.

    Returns:
        float: Annual rainfall in mm, or None if the request fails.
    """
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365)

    params = {
        "latitude":  lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date":   today.strftime("%Y-%m-%d"),
        "daily":     "precipitation_sum",
        "timezone":  "auto",
    }

    try:
        resp = requests.get(_ARCHIVE_URL, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            daily_values = data.get("daily", {}).get("precipitation_sum", [])
            # Filter out None entries (missing days) and sum
            total = sum(v for v in daily_values if v is not None)
            return round(total, 1)
    except requests.exceptions.RequestException:
        pass
    return None


def fetch_weather_data(city_name: str) -> dict:
    """
    Fetch current temperature, humidity, and annual rainfall estimate for a
    city or district.

    Temperature and humidity come from OpenWeatherMap Current Weather API.
    Annual rainfall comes from Open-Meteo Historical Archive (last 365 days).

    Args:
        city_name (str): Name of the city or district (e.g. "Thanjavur").

    Returns:
        dict with keys:
            temperature  (float)  — degrees Celsius
            humidity     (float)  — relative humidity %
            rainfall     (float)  — annual rainfall in mm/year (ML model input)
            rainfall_source (str) — "open_meteo" | "default_fallback"
        On failure, returns {"error": "<message>"}.
    """
    if not city_name:
        return {"error": "City or district name is required."}

    if not _OW_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is not set. Add it to your .env file."}

    # --- Step 1: Current weather (temperature + humidity) ---
    try:
        ow_resp = requests.get(
            _OW_BASE_URL,
            params={"q": city_name, "appid": _OW_API_KEY, "units": "metric"},
            timeout=10,
        )
        if ow_resp.status_code != 200:
            return {
                "error": f"OpenWeather API returned {ow_resp.status_code}",
                "message": ow_resp.json().get("message", "Unknown error"),
            }
        ow_data = ow_resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Connection to OpenWeather API timed out."}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to OpenWeather API."}
    except requests.exceptions.RequestException as exc:
        return {"error": f"OpenWeather API error: {exc}"}

    temperature = ow_data.get("main", {}).get("temp")
    humidity    = ow_data.get("main", {}).get("humidity")

    # --- Step 2: Annual rainfall via Open-Meteo (no API key needed) ---
    coords = _geocode(city_name)
    annual_rainfall = None
    rainfall_source = "default_fallback"

    if coords:
        lat, lon = coords
        annual_rainfall = fetch_annual_rainfall(lat, lon)
        if annual_rainfall is not None:
            rainfall_source = "open_meteo"

    return {
        "temperature":     temperature,
        "humidity":        humidity,
        # rainfall is annual mm/year — directly compatible with ML model feature
        "rainfall":        annual_rainfall,     # None triggers fallback in orchestrator
        "rainfall_source": rainfall_source,
    }


if __name__ == "__main__":
    city = "Thanjavur"
    print(f"Fetching weather for: {city}...")
    result = fetch_weather_data(city)
    print("Result:", result)
