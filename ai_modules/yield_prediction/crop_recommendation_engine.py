"""
crop_recommendation_engine.py — Crop scoring and ranking engine.

For each candidate crop, computes a recommendation score:

    score = (predicted_yield_t_ha × market_price_INR) / supply_index

Then returns the top 3 crops sorted by score descending.

All sub-module calls use absolute package-level imports so this module runs
correctly whether invoked as a script from the project root or imported by
the FastAPI layer.
"""

from ai_modules.yield_prediction.predict_model       import predict_crop_yield
from ai_modules.yield_prediction.agmarknet_price_service import fetch_crop_price
from ai_modules.yield_prediction.supply_analysis     import get_supply_index
from ai_modules.yield_prediction.market_balance_engine   import analyze_market_balance


def recommend_crops(
    state: str,
    district: str,
    crop_list: list[str],
    weather_inputs: dict,
) -> list[dict]:
    """
    Recommend the best crops for a farmer based on yield prediction, market
    price, and regional supply data.

    Args:
        state          (str):  Name of the target state.
        district       (str):  Name of the target district.
        crop_list      (list): Crop names to evaluate.
        weather_inputs (dict): Keys: 'year', 'rainfall' (mm/year), 'pesticides', 'temperature'.

    Returns:
        list[dict]: Top 3 recommended crops, sorted by score descending.
                    Each entry contains: crop, predicted_yield, market_price,
                    supply_index, supply_level, market_recommendation,
                    expected_revenue, score.
    """
    results = []

    year        = weather_inputs.get("year",        2026)
    rainfall    = weather_inputs.get("rainfall",    1000)
    pesticides  = weather_inputs.get("pesticides",  100)
    temperature = weather_inputs.get("temperature", 25)

    for crop in crop_list:
        # 1. Predict Yield
        # ML model returns hg/ha — convert to t/ha (* 0.0001) for human-readable output.
        raw_yield = predict_crop_yield(year, rainfall, pesticides, temperature, crop)

        if isinstance(raw_yield, str) or raw_yield is None:
            # Unsupported crop or model error — include in results with 0 yield
            # so the caller still gets a complete response for every requested crop.
            predicted_yield = 0.0
        else:
            predicted_yield = float(raw_yield) * 0.0001

        # 2. Fetch real-time market price
        price_data   = fetch_crop_price(crop, state=state, district=district)
        market_price = 0.0

        if "error" not in price_data and price_data.get("modal_price") != "N/A":
            try:
                market_price = float(price_data.get("modal_price", 0.0))
            except (ValueError, TypeError):
                market_price = 0.0

        # 3. Get regional supply index
        supply_index = get_supply_index(crop, state, district)

        # Pad supply to 1.0 to avoid ZeroDivisionError when a crop has no history
        safe_supply = float(supply_index) if supply_index and supply_index > 0 else 1.0

        # 4. Calculate expected revenue and recommendation score
        expected_revenue = predicted_yield * market_price
        score            = expected_revenue / safe_supply

        # 5. Market balance classification
        balance_metrics = analyze_market_balance(supply_index)

        results.append({
            "crop":                  crop,
            "predicted_yield":       round(predicted_yield, 2),
            "market_price":          round(market_price, 2),
            "supply_index":          round(supply_index if supply_index else 0.0, 4),
            "supply_level":          balance_metrics["supply_level"],
            "market_recommendation": balance_metrics["market_recommendation"],
            "expected_revenue":      round(expected_revenue, 2),
            "score":                 round(score, 2),
        })

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    return sorted_results[:3]


if __name__ == "__main__":
    test_state    = "Uttar Pradesh"
    test_district = "KANPUR NAGAR"
    test_crops    = ["Rice, paddy", "Maize", "Wheat", "Potatoes"]

    test_weather = {
        "year":        2026,
        "rainfall":    1500,
        "pesticides":  120,
        "temperature": 28,
    }

    print(f"--- Running Crop Recommendation Engine ---")
    print(f"Region: {test_district}, {test_state}")
    print(f"Analyzing Crops: {', '.join(test_crops)}\n")

    top_crops = recommend_crops(
        state=test_state,
        district=test_district,
        crop_list=test_crops,
        weather_inputs=test_weather,
    )

    print("--- Top 3 Recommended Crops ---")
    for idx, crop_data in enumerate(top_crops, 1):
        print(f"\n[{idx}] Crop: {crop_data['crop']}")
        print(f"    Predicted Yield:  {crop_data['predicted_yield']} t/ha")
        print(f"    Market Price:     ₹{crop_data['market_price']}")
        print(f"    Supply Index:     {crop_data['supply_index']}")
        print(f"    Expected Revenue: ₹{crop_data['expected_revenue']}")
        print(f"    Score:            {crop_data['score']}")
