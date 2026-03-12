import os
import requests
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import CROP_ALIAS

API_KEY = os.getenv("AGMARKNET_API_KEY", "REMOVED_SECRET")
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRICE_DATASET_PATH = os.path.join(BASE_DIR, "dataset", "Agriculture_price_dataset.csv")

# Loaded once globally — avoids reloading the large CSV on every fallback call
fallback_df = None

def load_fallback_db():
    global fallback_df
    if fallback_df is None:
        try:
            fallback_df = pd.read_csv(PRICE_DATASET_PATH)
        except Exception:
            fallback_df = pd.DataFrame()

def get_fallback_price(crop_name):
    """Return the mean Modal_Price from the local dataset for a given crop name."""
    load_fallback_db()

    if fallback_df is None or fallback_df.empty:
        return 0.0

    normalized_crop = CROP_ALIAS.get(crop_name, crop_name)

    mask = fallback_df['Commodity'].str.lower().str.contains(normalized_crop.lower(), na=False)
    filtered_data = fallback_df[mask]

    if filtered_data.empty:
        return 0.0

    filtered_data = filtered_data.copy()
    filtered_data['Modal_Price'] = pd.to_numeric(filtered_data['Modal_Price'], errors='coerce')
    avg_price = filtered_data['Modal_Price'].mean()

    return 0.0 if pd.isna(avg_price) else float(avg_price)

def fetch_crop_price(crop_name, state=None, district=None, market=None):
    """
    Fetch real-time crop prices from the Agmarknet API with automatic dataset fallback.

    Returns:
        dict: {"crop", "market", "modal_price", "source"} — always JSON-serializable.
    """
    if not crop_name:
        return {"error": "Crop name is required."}

    normalized_crop = CROP_ALIAS.get(crop_name, crop_name)

    result = {
        "crop": crop_name,
        "market": market if market else "Generic Market",
        "modal_price": 0.0,
        "source": "API"
    }

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 100,
        "filters[commodity]": normalized_crop
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
        response = requests.get(BASE_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") != "error":
                records = data.get("records", [])
                if records:
                    highest_price = -1.0
                    for record in records:
                        commodity = record.get("commodity", record.get("Commodity", ""))
                        if normalized_crop.lower() in commodity.lower():
                            raw_price = record.get("modal_price", record.get("Modal_Price", 0))
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
            result["crop"] = crop_name
            result["market"] = best_record.get("market", best_record.get("Market", "Unknown Market"))
            result["modal_price"] = raw_modal
            result["source"] = "API"
            return result
        else:
            api_failed = True

    # --- Dataset fallback ---
    fallback_avg = get_fallback_price(crop_name)
    if fallback_avg > 0:
        result["market"] = "National Average (Dataset)"
        result["modal_price"] = round(fallback_avg, 2)
        result["source"] = "Dataset"
    else:
        result["market"] = "Unknown"
        result["modal_price"] = 0.0
        result["source"] = "Dataset (No Data)"

    return result

if __name__ == "__main__":
    print("Testing fetch_crop_price ('Tomato')...")
    print(fetch_crop_price(crop_name="Tomato", state="Maharashtra"))

    print("\nTesting fallback ('Rice, paddy' with invalid state)...")
    print(fetch_crop_price(crop_name="Rice, paddy", state="OfflineState"))