import sys
import os

# Ensure local imports work correctly relative to the current module execution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from predict_model import predict_crop_yield
from agmarknet_price_service import fetch_crop_price
from supply_analysis import get_supply_index
from market_balance_engine import analyze_market_balance

def recommend_crops(state, district, crop_list, weather_inputs):
    """
    Recommend the best crops for a farmer based on yield prediction, market price, and regional supply data.
    
    Args:
        state (str): Name of the target state.
        district (str): Name of the target district.
        crop_list (list): List of crop string names to evaluate.
        weather_inputs (dict): Dictionary tracking 'year', 'rainfall', 'pesticides', and 'temperature'.
        
    Returns:
        list: A sorted list containing the top 3 recommended crops formatted natively as dictionaries.
    """
    results = []
    
    # Extract weather inputs natively, defaulting safely if keys are missing
    year = weather_inputs.get("year", 2026)
    rainfall = weather_inputs.get("rainfall", 1000)
    pesticides = weather_inputs.get("pesticides", 100)
    temperature = weather_inputs.get("temperature", 25)

    for crop in crop_list:
        # 1. Predict Yield
        # The ML model returns hg/ha. Convert to tons/hectare for standard scaling (* 0.0001).
        raw_yield = predict_crop_yield(year, rainfall, pesticides, temperature, crop)
        
        if isinstance(raw_yield, str) or raw_yield is None:
            predicted_yield = 0.0
        else:
            predicted_yield = float(raw_yield) * 0.0001
            
        # 2. Fetch real-time market price
        price_data = fetch_crop_price(crop, state=state, district=district)
        market_price = 0.0
        
        if "error" not in price_data and price_data.get("modal_price") != "N/A":
            try:
                market_price = float(price_data.get("modal_price", 0.0))
            except ValueError:
                market_price = 0.0
                
        # 3. Get regional supply index tracking dataset capacity
        supply_index = get_supply_index(crop, state, district)
        
        # Safely pad supply tracking to prevent math `DivisionByZero` errors natively if a crop isn't currently produced 
        safe_supply = float(supply_index) if supply_index and supply_index > 0 else 1.0
        
        # 4. Calculate actionable revenue bounds
        expected_revenue = predicted_yield * market_price
        
        # 5. Core Recommendation Formula: (predicted_yield * market_price) / supply_index
        score = expected_revenue / safe_supply
        
        # Determine strict market balance intelligence bounds
        balance_metrics = analyze_market_balance(supply_index)
        
        # Assemble dictionary standard mapping identically to required format structure
        results.append({
            "crop": crop,
            "predicted_yield": round(predicted_yield, 2),
            "market_price": round(market_price, 2),
            "supply_index": round(supply_index if supply_index else 0.0, 4),
            "supply_level": balance_metrics['supply_level'],
            "market_recommendation": balance_metrics['market_recommendation'],
            "expected_revenue": round(expected_revenue, 2),
            "score": round(score, 2)
        })

        
    # Sort results by score strictly descending explicitly returning only top 3 evaluations
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    return sorted_results[:3]

if __name__ == "__main__":
    # Test block evaluation strictly analyzing local parameters
    test_state = "Tamil Nadu"
    test_district = "Thanjavur"
    test_crops = ["Rice, paddy","Maize","Wheat","Potatoes"]
    
    test_weather = {
        "year": 2026,
        "rainfall": 1500,
        "pesticides": 120,
        "temperature": 28
    }
    
    print(f"--- Running Crop Recommendation Engine ---")
    print(f"Region: {test_district}, {test_state}")
    print(f"Analyzing Crops: {', '.join(test_crops)}\n")
    
    top_crops = recommend_crops(
        state=test_state, 
        district=test_district, 
        crop_list=test_crops, 
        weather_inputs=test_weather
    )
    
    print("--- Top 3 Recommended Crops ---")
    for idx, crop_data in enumerate(top_crops, 1):
        print(f"\n[{idx}] Crop: {crop_data['crop']}")
        print(f"    Predicted Yield:  {crop_data['predicted_yield']} tons/ha")
        print(f"    Market Price:     ₹{crop_data['market_price']}")
        print(f"    Supply Index:     {crop_data['supply_index']}")
        print(f"    Expected Revenue: ₹{crop_data['expected_revenue']}")
        print(f"    Score:            {crop_data['score']}")
