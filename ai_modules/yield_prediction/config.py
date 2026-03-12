"""
config.py — Shared configuration for all TrustAgri AI modules.

Import from this file instead of duplicating constants across modules.
"""

# Crop name alias mapping: normalizes ML model names to dataset/API-friendly names.
# Add new aliases here — they apply across agmarknet_price_service and supply_analysis.
CROP_ALIAS = {
    "Rice, paddy": "Rice",
    "Potatoes": "Potato",
    "Tomatoes": "Tomato",
    "Onions, dry": "Onion"
}

# Default crop list evaluated by the recommendation engine
DEFAULT_CROP_LIST = ["Rice, paddy", "Maize", "Wheat", "Potatoes"]

# Safe weather defaults used when the OpenWeather API is unavailable
DEFAULT_WEATHER = {
    "temperature": 28.0,
    "rainfall": 1000.0,   # Annual mm estimate used as fallback
    "humidity": 60.0,
    "pesticides": 100     # Default pesticide usage in tonnes
}
