import pandas as pd
import os
from config import CROP_ALIAS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "India Agriculture Crop Production.csv")

def load_and_clean_data():
    """Load and clean the crop production dataset, computing supply_index per row."""
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return None

    df = df.dropna(subset=['Area', 'Production'])
    df['Area'] = pd.to_numeric(df['Area'], errors='coerce')
    df['Production'] = pd.to_numeric(df['Production'], errors='coerce')
    df = df.dropna(subset=['Area', 'Production'])
    df = df[df['Area'] > 0]
    df['supply_index'] = df['Production'] / df['Area']
    return df

# Load dataset once at module import
crop_df = load_and_clean_data()

def get_supply_index(crop, state, district):
    """
    Return the average supply_index for a crop in a given state/district.

    Args:
        crop (str): Crop name (will be normalized via CROP_ALIAS).
        state (str): State name.
        district (str): District name.

    Returns:
        float | None: Average supply index, or None if no data found.
    """
    if crop_df is None or crop_df.empty:
        return None

    normalized_crop = CROP_ALIAS.get(crop.strip(), crop.strip())

    mask = (
        (crop_df['State'].str.strip().str.lower() == state.strip().lower()) &
        (crop_df['District'].str.strip().str.lower() == district.strip().lower()) &
        (crop_df['Crop'].str.lower().str.contains(normalized_crop.lower(), na=False))
    )

    filtered_df = crop_df[mask]
    if filtered_df.empty:
        return None

    return float(filtered_df['supply_index'].mean())

def get_region_crop_supply(state, district):
    """
    Return a dict mapping every crop in a region to its average supply_index.

    Returns:
        dict: {"CropName": supply_index_float, ...}
    """
    if crop_df is None or crop_df.empty:
        return {}

    mask = (
        (crop_df['State'].str.strip().str.lower() == state.strip().lower()) &
        (crop_df['District'].str.strip().str.lower() == district.strip().lower())
    )

    filtered_df = crop_df[mask]
    if filtered_df.empty:
        return {}

    return filtered_df.groupby('Crop')['supply_index'].mean().to_dict()

if __name__ == "__main__":
    test_state = "Tamil Nadu"
    test_district = "Thanjavur"

    print(f"--- Supply Analysis for {test_state}, {test_district} ---")

    rice_supply = get_supply_index("Rice, paddy", test_state, test_district)
    print(f"\n[+] Supply Index for Rice, paddy: {rice_supply if rice_supply is not None else 'Not Found'}")

    region_supply = get_region_crop_supply(test_state, test_district)
    if region_supply:
        sorted_supply = sorted(region_supply.items(), key=lambda x: x[1], reverse=True)
        print("\n[+] Top 5 Crops with Highest Supply Index:")
        for idx, (crop_name, supply_val) in enumerate(sorted_supply[:5], 1):
            print(f"    {idx}. {crop_name}: {supply_val:.4f}")
    else:
        print("\n[-] No crop data found for the requested region.")
