import datetime
from weather_service import fetch_weather_data
from predict_model import predict_crop_yield
from agmarknet_price_service import fetch_crop_price
from supply_analysis import get_supply_index
from crop_recommendation_engine import recommend_crops
from risk_analysis import analyze_risk

def run_system_validation():
    # 2. Testing locations explicitly matrixed natively
    locations = [
        ("Tamil Nadu", "Thanjavur"),
        ("Maharashtra", "Pune"),
        ("Punjab", "Ludhiana"),
        ("Karnataka", "Bangalore")
    ]
    
    # 3. Explicit crops tracking across validation architectures
    crop_list = ["Rice, paddy", "Maize", "Wheat", "Potatoes"]
    
    # Trace variables securing explicit metrics
    price_errors = 0
    supply_errors = 0
    weather_errors = 0
    
    total_locations = len(locations)
    total_crops = len(crop_list) * total_locations
    current_year = datetime.datetime.now().year
    
    print("=" * 60)
    print("      TrustAgri System Validation Test execution trace     ")
    print("=" * 60)
    
    # 4. Loop across identical parameter limits
    for state, district in locations:
        print(f"\nEvaluating Location: {district}, {state}")
        print("-" * 60)
        
        # Step 1: Fetch Weather Data automatically
        weather_data = fetch_weather_data(district)
        
        if "error" in weather_data:
            print("  [Warning] Weather API failure. Using safe default weather values.")
            weather_errors += 1
            temperature = 28.0
            rainfall = 1000.0
            humidity = 60.0
        else:
            temperature = weather_data.get("temperature", 28.0)
            raw_rain = weather_data.get("rainfall", 0.0)
            rainfall = raw_rain if raw_rain > 0 else 1000.0
            humidity = weather_data.get("humidity", 60.0)
            
        weather_inputs = {
            "year": current_year,
            "rainfall": rainfall,
            "temperature": temperature,
            "pesticides": 100
        }
        
        # Execute unified recommendation array strictly ensuring the engine handles variables cleanly securely
        # By processing Step 5 (Engine), we identically process Steps 2, 3, AND 4 natively securely mapping the exact required variables!
        recommendations = recommend_crops(state, district, crop_list, weather_inputs)
        
        # Secure outputs manually bypassing any skipped arrays to fulfill raw execution trace requests identically
        for crop in crop_list:
            print(f"\n  [Crop] {crop}")
            
            # Step 2: Yield prediction
            raw_yield = predict_crop_yield(current_year, rainfall, weather_inputs["pesticides"], temperature, crop)
            if isinstance(raw_yield, str) or raw_yield is None:
                predicted_yield = 0.0
            else:
                predicted_yield = float(raw_yield) * 0.0001
                
            # Step 3: Fetch market price
            price_data = fetch_crop_price(crop, state, district)
            price = 0.0
            if "error" not in price_data and price_data.get("modal_price") != "N/A":
                try:
                    price = float(price_data.get("modal_price", 0.0))
                except ValueError:
                    price = 0.0
                    
            if price == 0:
                print("  [Warning] Price fallback triggered or data missing")
                price_errors += 1
                
            # Step 4: Supply Analysis tracking securely
            supply_index = get_supply_index(crop, state, district)
            supply_val = float(supply_index) if supply_index else 0.0
            
            if supply_val == 0:
                print("  [Warning] Supply dataset missing crop mapping")
                supply_errors += 1
                
            # Ensure expected logic loops explicitly
            expected_revenue = predicted_yield * price
            
            # Step 6: Risk Analysis inherently checking the values explicitly
            risk_dict = analyze_risk(temperature, rainfall, price)
            risk_level = risk_dict["risk_level"]
            
            # 5. Print explicit matrix mapping natively
            print(f"    Predicted Yield : {predicted_yield:.2f} t/ha")
            print(f"    Market Price    : ₹{price:.2f}")
            print(f"    Supply Index    : {supply_val:.4f}")
            print(f"    Expected Revenue: ₹{expected_revenue:.2f}")
            print(f"    Risk Level      : {risk_level}")

    # 7. Final Summary trace matrix natively explicitly tracking limits
    print("\n========================================")
    print("         Test Results Summary")
    print("========================================")
    print(f"Locations tested:     {total_locations}")
    print(f"Crops tested:         {total_crops}")
    print(f"Price errors:         {price_errors}")
    print(f"Supply errors:        {supply_errors}")
    print(f"Weather API failures: {weather_errors}")
    print("========================================")

if __name__ == "__main__":
    run_system_validation()
