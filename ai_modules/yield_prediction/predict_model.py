import os
import joblib
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "yield_model.pkl")
encoder_path = os.path.join(BASE_DIR, "crop_encoder.pkl")

# Load the trained model once at module import — not on every call
try:
    model = joblib.load(model_path)
except FileNotFoundError:
    print(f"Error: Model not found at {model_path}. Please run train_model.py first.")
    model = None

# Load the fitted LabelEncoder once at module import — eliminates the CSV re-fit on every prediction
try:
    label_encoder = joblib.load(encoder_path)
except FileNotFoundError:
    print(f"Warning: Encoder not found at {encoder_path}. Please run train_model.py first.")
    label_encoder = None

def predict_crop_yield(year, rainfall, pesticides, temperature, crop_name):
    """
    Predict crop yield using the trained RandomForest model.

    Args:
        year (int): Target year.
        rainfall (float): Annual rainfall in mm (or monthly approximation).
        pesticides (float): Pesticide usage in tonnes.
        temperature (float): Average temperature in Celsius.
        crop_name (str): Crop name (must match training dataset labels).

    Returns:
        float: Predicted yield in hg/ha, or a string error message.
    """
    if model is None:
        return "Model not loaded. Please run train_model.py first."

    if label_encoder is None:
        return "Encoder not loaded. Please run train_model.py first."

    # Encode crop name using the pre-fitted encoder — O(1), no CSV reload
    try:
        encoded_crop = label_encoder.transform([crop_name])[0]
    except ValueError as e:
        print(f"Error encoding crop name: {e}")
        return f"Unknown crop: {crop_name}"

    # Prepare the feature DataFrame in training column order
    features = pd.DataFrame([{
        'Year': year,
        'average_rain_fall_mm_per_year': rainfall,
        'pesticides_tonnes': pesticides,
        'avg_temp': temperature,
        'Item': encoded_crop
    }])

    prediction = model.predict(features)
    return prediction[0]

if __name__ == "__main__":
    print("Testing crop yield prediction...")
    predicted_yield = predict_crop_yield(
        year=2024,
        rainfall=1500,
        pesticides=120,
        temperature=16,
        crop_name="Rice, paddy"
    )
    print(f"Predicted Yield for Rice, paddy: {predicted_yield} hg/ha")
