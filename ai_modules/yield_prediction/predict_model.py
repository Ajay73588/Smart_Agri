"""
predict_model.py — Crop yield inference using the trained RandomForest model.

Loads yield_model.pkl and crop_encoder.pkl once at module import time.

Model artifacts are stored in the `models/` directory at the project root
(resolved via config.MODELS_DIR).

Units:
    Input  — rainfall: mm/year (annual total), temperature: °C, pesticides: tonnes
    Output — yield in hg/ha (hectograms per hectare)
    The caller is responsible for unit conversion; typically × 0.0001 → t/ha.
"""

import os
import joblib
import pandas as pd

from ai_modules.yield_prediction.config import MODELS_DIR

MODEL_PATH   = os.path.join(MODELS_DIR, "yield_model.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "crop_encoder.pkl")

# ---------------------------------------------------------------------------
# Load model and encoder once at module import — not on every call
# ---------------------------------------------------------------------------
try:
    _model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    print(f"[predict_model] Error: Model not found at {MODEL_PATH}. Run train_model.py first.")
    _model = None

try:
    _label_encoder = joblib.load(ENCODER_PATH)
except FileNotFoundError:
    print(f"[predict_model] Warning: Encoder not found at {ENCODER_PATH}. Run train_model.py first.")
    _label_encoder = None


def get_supported_crops() -> list[str]:
    """Return the list of crop names the model was trained on."""
    if _label_encoder is None:
        return []
    return list(_label_encoder.classes_)


def predict_crop_yield(
    year: int,
    rainfall: float,
    pesticides: float,
    temperature: float,
    crop_name: str,
) -> float | str:
    """
    Predict crop yield using the trained RandomForest model.

    Args:
        year        (int):   Target year.
        rainfall    (float): Annual rainfall in mm/year (matches training data).
        pesticides  (float): Pesticide usage in tonnes.
        temperature (float): Average temperature in Celsius.
        crop_name   (str):   Crop name — must match training dataset labels exactly.

    Returns:
        float: Predicted yield in hg/ha.
        str:   Error message string if model/encoder unavailable or crop unknown.
    """
    if _model is None:
        return "Model not loaded. Please run train_model.py first."

    if _label_encoder is None:
        return "Encoder not loaded. Please run train_model.py first."

    # --- Input validation: reject unknown crop names early ---
    if crop_name not in _label_encoder.classes_:
        supported = ", ".join(sorted(_label_encoder.classes_)[:10])
        return (
            f"Unsupported crop: '{crop_name}'. "
            f"The model supports {len(_label_encoder.classes_)} crops. "
            f"Examples: {supported} ..."
        )

    encoded_crop = _label_encoder.transform([crop_name])[0]

    features = pd.DataFrame([{
        "Year":                        year,
        "average_rain_fall_mm_per_year": rainfall,
        "pesticides_tonnes":           pesticides,
        "avg_temp":                    temperature,
        "Item":                        encoded_crop,
    }])

    prediction = _model.predict(features)
    return float(prediction[0])


if __name__ == "__main__":
    print("Testing crop yield prediction...")
    predicted_yield = predict_crop_yield(
        year=2024,
        rainfall=1500,
        pesticides=120,
        temperature=16,
        crop_name="Rice, paddy",
    )
    print(f"Predicted Yield for Rice, paddy: {predicted_yield} hg/ha")
    print(f"Unsupported crop test: {predict_crop_yield(2024, 1500, 120, 16, 'Dragonfruit')}")
