"""
config.py — Shared configuration for all TrustAgri AI modules.

Import from this file instead of duplicating constants across modules.
"""
import os

# ---------------------------------------------------------------------------
# Project root — resolved once so all modules can build absolute paths
# from this single source of truth regardless of where they are invoked from.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------------------------------------------------------------------------
# Data & model directories (relative to project root)
# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# ---------------------------------------------------------------------------
# Crop name alias mapping: normalises ML model crop names to the names used
# in the Agmarknet API and the production CSV dataset.
# Add new aliases here — they apply across agmarknet_price_service and
# supply_analysis automatically.
# ---------------------------------------------------------------------------
CROP_ALIAS = {
    "Rice, paddy": "Rice",
    "Potatoes":    "Potato",
    "Tomatoes":    "Tomato",
    "Onions, dry": "Onion",
}

# ---------------------------------------------------------------------------
# Default crop list evaluated by the recommendation engine
# ---------------------------------------------------------------------------
DEFAULT_CROP_LIST = ["Rice, paddy", "Maize", "Wheat", "Potatoes"]

# ---------------------------------------------------------------------------
# Safe weather defaults used when external APIs are unavailable.
# rainfall: annual mm estimate (matches ML training data scale).
# ---------------------------------------------------------------------------
DEFAULT_WEATHER = {
    "temperature": 28.0,
    "rainfall":    1000.0,  # Annual mm — used as fallback when Open-Meteo fails
    "humidity":    60.0,
    "pesticides":  100,     # Default pesticide usage in tonnes
}
