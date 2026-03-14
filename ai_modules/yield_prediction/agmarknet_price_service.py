"""
agmarknet_price_service.py — Crop price fetching with CSV fallback.

Primary source: Agmarknet API (data.gov.in resource 9ef84268-...).
Fallback: Local Agriculture_price_dataset.csv when the API is unavailable.

API key is loaded exclusively from the AGMARKNET_API_KEY environment variable.
Set this in your .env file (see .env.example).  The application will raise a
RuntimeError at startup if the key is missing.
"""

import os
import requests
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ai_modules.yield_prediction.config import CROP_ALIAS, DATA_DIR

# ---------------------------------------------------------------------------
# API credentials — loaded from environment only (no hardcoded fallback)
# ---------------------------------------------------------------------------
_API_KEY = os.getenv("AGMARKNET_API_KEY")
_BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# ---------------------------------------------------------------------------
# Fallback dataset path — resolved from DATA_DIR in config
# ---------------------------------------------------------------------------
PRICE_DATASET_PATH = os.path.join(DATA_DIR, "Agriculture_price_dataset.csv")

# Loaded once globally — avoids reloading the 53 MB CSV on every fallback call
_fallback_df = None


def _load_fallback_db() -> None:
    global _fallback_df
    if _fallback_df is None:
        try:
            _fallback_df = pd.read_csv(PRICE_DATASET_PATH)
        except Exception:
            _fallback_df = pd.DataFrame()


def get_fallback_price(crop_name: str) -> float:
    """Return the mean Modal_Price from the local dataset for a given crop name."""
    _load_fallback_db()

    if _fallback_df is None or _fallback_df.empty:
        return 0.0

    normalized_crop = CROP_ALIAS.get(crop_name, crop_name)
    mask = _fallback_df["Commodity"].str.lower().str.contains(
        normalized_crop.lower(), na=False
    )
    filtered_data = _fallback_df[mask]

    if filtered_data.empty:
        return 0.0

    filtered_data = filtered_data.copy()
    filtered_data["Modal_Price"] = pd.to_numeric(
        filtered_data["Modal_Price"], errors="coerce"
    )
    avg_price = filtered_data["Modal_Price"].mean()
    return 0.0 if pd.isna(avg_price) else float(avg_price)


def fetch_crop_price(
    crop_name: str,
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
) -> dict:
    """
    Fetch real-time crop prices from the Agmarknet API with automatic
    dataset fallback.

    Args:
        crop_name (str): Crop to query (e.g. "Rice, paddy").
        state     (str): Optional state filter.
        district  (str): Optional district filter.
        market    (str): Optional market filter.

    Returns:
        dict: {"crop", "market", "modal_price", "source"} — always JSON-serializable.

    Raises:
        RuntimeError: If AGMARKNET_API_KEY is not set in the environment.
    """
    if not crop_name:
        return {"error": "Crop name is required."}

    if not _API_KEY:
        raise RuntimeError(
            "AGMARKNET_API_KEY is not set. "
            "Add it to your .env file (see .env.example)."
        )

    normalized_crop = CROP_ALIAS.get(crop_name, crop_name)

    result = {
        "crop":        crop_name,
        "market":      market if market else "Generic Market",
        "modal_price": 0.0,
        "source":      "API",
    }

    params = {
        "api-key":           _API_KEY,
        "format":            "json",
        "limit":             100,
        "filters[commodity]": normalized_crop,
    }
    if state:
        params["filters[state]"] = state
    if district:
        params["filters[district]"] = district
    if market:
        params["filters[market]"] = market

    api_failed = False
    best_record = None

    try:
        response = requests.get(_BASE_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") != "error":
                records = data.get("records", [])
                if records:
                    highest_price = -1.0
                    for record in records:
                        commodity = record.get("commodity", record.get("Commodity", ""))
                        if normalized_crop.lower() in commodity.lower():
                            raw_price = record.get(
                                "modal_price", record.get("Modal_Price", 0)
                            )
                            try:
                                price_val = float(raw_price)
                            except (ValueError, TypeError):
                                price_val = 0.0
                            if price_val > highest_price:
                                highest_price = price_val
                                best_record = record
                else:
                    api_failed = True
            else:
                api_failed = True
        else:
            api_failed = True

    except (requests.exceptions.RequestException, ValueError):
        api_failed = True

    if not api_failed and best_record:
        raw_modal = best_record.get("modal_price", best_record.get("Modal_Price", 0.0))
        try:
            raw_modal = float(raw_modal)
        except ValueError:
            raw_modal = 0.0

        if raw_modal > 0:
            result["crop"]        = crop_name
            result["market"]      = best_record.get("market", best_record.get("Market", "Unknown Market"))
            result["modal_price"] = raw_modal
            result["source"]      = "API"
            return result
        else:
            api_failed = True

    # --- Dataset fallback ---
    fallback_avg = get_fallback_price(crop_name)
    if fallback_avg > 0:
        result["market"]      = "National Average (Dataset)"
        result["modal_price"] = round(fallback_avg, 2)
        result["source"]      = "Dataset"
    else:
        result["market"]      = "Unknown"
        result["modal_price"] = 0.0
        result["source"]      = "Dataset (No Data)"

    return result


if __name__ == "__main__":
    print("Testing fetch_crop_price ('Tomato')...")
    print(fetch_crop_price(crop_name="Tomato", state="Maharashtra"))

    print("\nTesting fallback ('Rice, paddy' with invalid state)...")
    print(fetch_crop_price(crop_name="Rice, paddy", state="OfflineState"))