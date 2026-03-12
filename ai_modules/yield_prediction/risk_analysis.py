def analyze_risk(temperature, rainfall, price):
    """
    Estimate farming risk based on active weather and regional market conditions.
    
    Args:
        temperature (float): Current ambient temperature in Celsius.
        rainfall (float): Measured rainfall metrics in mm.
        price (float): The current modal market price for the evaluated commodity.
        
    Returns:
        dict: A dictionary mapping the 'risk_level' strictly and providing a 'reason'.
    """
    
    # 1. Rainfall boundaries evaluation
    if rainfall < 400 or rainfall > 2500:
        return {
            "risk_level": "High",
            "reason": "Rainfall outside optimal farming range (400mm - 2500mm)"
        }
        
    # 2. Temperature tolerance evaluation
    if temperature < 10 or temperature > 40:
        return {
            "risk_level": "Medium",
            "reason": "Temperature slightly outside optimal farming range"
        }
        
    # 3. Market viability evaluation
    if price < 500:
        return {
            "risk_level": "Medium",
            "reason": "Market price is considered too low for optimal revenue"
        }
        
    # 4. Optimal conditions native fallback
    return {
        "risk_level": "Low",
        "reason": "Favorable farming conditions mapping high viability"
    }

if __name__ == "__main__":
    # Test cases evaluating script structure natively
    print(analyze_risk(35, 1200, 600))  # Expected: Low
    print(analyze_risk(45, 1200, 600))  # Expected: Medium (temp > 40)
    print(analyze_risk(30, 200, 800))   # Expected: High (rain < 400)
    print(analyze_risk(25, 1500, 400))  # Expected: Medium (price < 500)
