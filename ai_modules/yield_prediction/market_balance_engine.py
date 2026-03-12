def analyze_market_balance(supply_index):
    """
    Analyze supply levels of crops in a region and determine market balance.
    
    Args:
        supply_index (float | None): The computed regional supply scalar.
        
    Returns:
        dict: A dictionary mapping 'supply_level' and 'market_recommendation'.
    """
    if supply_index is None:
        return {
            "supply_level": "Unknown",
            "market_recommendation": "No historical supply data available."
        }
        
    if supply_index > 8:
        return {
            "supply_level": "Oversupplied",
            "market_recommendation": "Too many farmers grow this crop. Market price may drop."
        }
        
    if supply_index >= 3 and supply_index <= 8:
        return {
            "supply_level": "Balanced",
            "market_recommendation": "Supply is stable."
        }
        
    if supply_index < 3:
        return {
            "supply_level": "High Demand",
            "market_recommendation": "Few farmers grow this crop. Market demand is higher."
        }

if __name__ == "__main__":
    # Test block evaluation
    print(analyze_market_balance(None)) # Expected: Unknown
    print(analyze_market_balance(9.5))  # Expected: Oversupplied
    print(analyze_market_balance(5.2))  # Expected: Balanced
    print(analyze_market_balance(1.5))  # Expected: High Demand
