import pandas as pd
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "dataset", "yield_df.csv")
model_path = os.path.join(BASE_DIR, "yield_model.pkl")
encoder_path = os.path.join(BASE_DIR, "crop_encoder.pkl")

# 1. Load dataset using pandas
data = pd.read_csv(file_path)

# 2. Remove the column "Unnamed: 0" if it exists
if "Unnamed: 0" in data.columns:
    data = data.drop(columns=["Unnamed: 0"])

# 3. Use these features
features = ['Year', 'average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp', 'Item']

# 4. Target variable: hg/ha_yield
target = 'hg/ha_yield'

# Keep only needed columns
data = data[features + [target]].dropna()

X = data[features].copy()
y = data[target]

# 5. Encode the crop column (Item) using LabelEncoder
label_encoder = LabelEncoder()
X['Item'] = label_encoder.fit_transform(X['Item'])

# 6. Split dataset using train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training RandomForestRegressor model...")
# 7. Train a RandomForestRegressor model
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# Predict on test set
y_pred = model.predict(X_test)

# 8. Print model accuracy using r2_score
r2 = r2_score(y_test, y_pred)
print(f"Model R2 Score: {r2}")

# 9. Save the trained model using joblib
joblib.dump(model, model_path)
print(f"Model saved to: {model_path}")

# 10. Save the fitted LabelEncoder so predict_model.py can load it without re-fitting
joblib.dump(label_encoder, encoder_path)
print(f"Encoder saved to: {encoder_path}")
print(f"Encoder classes: {list(label_encoder.classes_[:5])} ... ({len(label_encoder.classes_)} total crops)")
print("Training complete.")