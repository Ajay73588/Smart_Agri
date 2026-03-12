AI Crop Profitability Engine

This module powers the AI decision system of TrustAgri.
It analyzes weather conditions, crop yield predictions, market prices, and supply-demand patterns to recommend the most profitable crops for farmers.

The goal is to help farmers choose crops that maximize revenue while minimizing risk.

Features Implemented
1. Weather Data Service

Purpose

Fetch real-time weather conditions for a given location.

Implementation

Uses OpenWeather API

Retrieves:

temperature

humidity

rainfall

Rainfall from the API (1-hour rainfall) is converted into a monthly rainfall estimate before being used in yield prediction.

Example logic:

rainfall_estimate = rainfall_1h * 24 * 30

This ensures compatibility with the ML model which expects larger rainfall values.

2. Crop Yield Prediction (Machine Learning)

Purpose

Predict the expected crop yield per hectare.

Implementation

Uses a trained machine learning model

Inputs include:

crop type

environmental conditions

rainfall estimate

To ensure fast predictions:

The trained model and LabelEncoder are saved using joblib

They are loaded once during prediction instead of retraining each time.

Example:

encoder = joblib.load("crop_encoder.pkl")
encoded_crop = encoder.transform([crop_name])
3. Market Price Retrieval

Purpose

Estimate the selling price of crops.

Implementation

Fetches prices using Agmarknet market data

If the API fails, the system falls back to a local dataset

This ensures the system always has price information.

4. Crop Supply Analysis

Purpose

Determine whether a crop is overproduced or in demand.

Implementation

Uses a historical agricultural production dataset.

Calculates a Supply Index:

Supply Index = Production / Area

Meaning:

Supply Index	Market Condition
High	Oversupply
Medium	Balanced
Low	High Demand
5. Market Demand Balancer

Purpose

Convert supply index into simple demand indicators.

Implementation

Based on the supply index the system classifies demand:

Low supply → High demand

Medium supply → Balanced demand

High supply → Oversupply

This prevents recommending crops that already have too much supply.

6. Risk Analysis

Purpose

Evaluate farming risk for each crop.

Implementation

Risk is estimated based on:

weather conditions

rainfall levels

market price stability

Output:

Low Risk
Medium Risk
High Risk
7. Crop Recommendation Engine

Purpose

Identify the most profitable crops.

Implementation

The engine combines:

predicted yield

market price

supply index

It calculates a profitability score:

score = (predicted_yield × market_price) / supply_index

Crops with high yield, high price, and low supply rank highest.

8. Revenue Forecast

Purpose

Calculate expected farmer revenue.

Implementation

For each crop:

expected_revenue = predicted_yield × market_price

The system outputs the Top 3 recommended crops.

Example Output
Top Recommended Crops

1. Potatoes
   Expected Revenue: ₹24,000
   Demand: High
   Risk: Low

2. Wheat
   Expected Revenue: ₹3,654
   Demand: Medium
   Risk: Low

3. Rice
   Expected Revenue: ₹3,136
   Demand: High
   Risk: Medium