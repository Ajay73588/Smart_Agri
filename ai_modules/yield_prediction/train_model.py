"""
train_model.py — Training script for the TrustAgri crop yield model.

Trains a RandomForestRegressor on the FAO-style crop yield dataset and saves:
  - models/yield_model.pkl    (trained RandomForestRegressor)
  - models/crop_encoder.pkl   (fitted LabelEncoder for crop names)

Run from the project root:
    python -m ai_modules.yield_prediction.train_model

Or directly:
    python ai_modules/yield_prediction/train_model.py
"""

import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

from ai_modules.yield_prediction.config import DATA_DIR, MODELS_DIR

# ---------------------------------------------------------------------------
# Paths — resolved via config constants, not relative to __file__
# ---------------------------------------------------------------------------
FILE_PATH    = os.path.join(DATA_DIR,   "yield_df.csv")
MODEL_PATH   = os.path.join(MODELS_DIR, "yield_model.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "crop_encoder.pkl")

# ---------------------------------------------------------------------------
# Features and target
# ---------------------------------------------------------------------------
FEATURES = ["Year", "average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp", "Item"]
TARGET   = "hg/ha_yield"


def train() -> None:
    print("=== TrustAgri — Model Training ===")

    # 1. Load dataset
    data = pd.read_csv(FILE_PATH)

    # 2. Drop unnamed index column if present
    if "Unnamed: 0" in data.columns:
        data = data.drop(columns=["Unnamed: 0"])

    # 3. Keep only needed columns, drop rows with nulls
    data = data[FEATURES + [TARGET]].dropna()

    X = data[FEATURES].copy()
    y = data[TARGET]

    # 4. Encode crop name (Item column) using LabelEncoder
    label_encoder = LabelEncoder()
    X["Item"] = label_encoder.fit_transform(X["Item"])

    # 5. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 6. Train
    print(f"Training RandomForestRegressor on {len(X_train):,} samples...")
    model = RandomForestRegressor(random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 7. Evaluate
    y_pred = model.predict(X_test)
    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Model R² Score : {r2:.4f}")
    print(f"Model MAE      : {mae:.2f} hg/ha")

    # 8. Persist model and encoder
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved    : {MODEL_PATH}")

    joblib.dump(label_encoder, ENCODER_PATH)
    print(f"Encoder saved  : {ENCODER_PATH}")
    print(f"Encoder classes: {list(label_encoder.classes_[:5])} ... ({len(label_encoder.classes_)} total crops)")
    print("Training complete.")


if __name__ == "__main__":
    train()