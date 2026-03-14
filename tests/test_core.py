"""
tests/test_core.py — pytest test suite for TrustAgri AI pipeline.

Converted from system_validation_test.py to a proper pytest module.

Test categories:
  - Unit tests (no network, no filesystem I/O beyond pre-loaded data)
  - Integration tests (require API keys in .env and internet access)

Run all unit tests (fast, offline):
    pytest tests/ -v -m "not integration"

Run everything including integration:
    pytest tests/ -v
"""

import sys
import os
import pytest

# Ensure project root is on path when running pytest from any directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ===========================================================================
# Unit Tests — pure logic, no network, no heavy I/O
# ===========================================================================

class TestRiskAnalysis:
    """Tests for the rule-based risk engine."""

    def setup_method(self):
        from ai_modules.yield_prediction.risk_analysis import analyze_risk
        self.analyze_risk = analyze_risk

    def test_low_risk_optimal_conditions(self):
        result = self.analyze_risk(temperature=25, rainfall=1200, price=800)
        assert result["risk_level"] == "Low"

    def test_high_risk_low_rainfall(self):
        result = self.analyze_risk(temperature=25, rainfall=200, price=800)
        assert result["risk_level"] == "High"

    def test_high_risk_excessive_rainfall(self):
        result = self.analyze_risk(temperature=25, rainfall=3000, price=800)
        assert result["risk_level"] == "High"

    def test_medium_risk_high_temperature(self):
        result = self.analyze_risk(temperature=45, rainfall=1200, price=800)
        assert result["risk_level"] == "Medium"

    def test_medium_risk_low_price(self):
        result = self.analyze_risk(temperature=25, rainfall=1200, price=300)
        assert result["risk_level"] == "Medium"

    def test_returns_dict_with_required_keys(self):
        result = self.analyze_risk(25, 1200, 800)
        assert "risk_level" in result
        assert "reason" in result


class TestMarketBalanceEngine:
    """Tests for the supply level classifier."""

    def setup_method(self):
        from ai_modules.yield_prediction.market_balance_engine import analyze_market_balance
        self.analyze = analyze_market_balance

    def test_none_supply_returns_unknown(self):
        result = self.analyze(None)
        assert result["supply_level"] == "Unknown"

    def test_oversupplied(self):
        result = self.analyze(9.5)
        assert result["supply_level"] == "Oversupplied"

    def test_balanced(self):
        result = self.analyze(5.0)
        assert result["supply_level"] == "Balanced"

    def test_high_demand(self):
        result = self.analyze(1.5)
        assert result["supply_level"] == "High Demand"

    def test_boundary_exactly_8(self):
        result = self.analyze(8.0)
        assert result["supply_level"] == "Balanced"

    def test_boundary_just_above_8(self):
        result = self.analyze(8.1)
        assert result["supply_level"] == "Oversupplied"


class TestPredictModel:
    """Tests for the ML inference wrapper."""

    def setup_method(self):
        from ai_modules.yield_prediction.predict_model import (
            predict_crop_yield,
            get_supported_crops,
        )
        self.predict  = predict_crop_yield
        self.get_crops = get_supported_crops

    def test_returns_float_for_valid_crop(self):
        result = self.predict(
            year=2024, rainfall=1200, pesticides=100, temperature=25,
            crop_name="Rice, paddy"
        )
        assert isinstance(result, float), f"Expected float, got: {result}"
        assert result > 0

    def test_unsupported_crop_returns_error_string(self):
        result = self.predict(
            year=2024, rainfall=1200, pesticides=100, temperature=25,
            crop_name="Dragonfruit_XYZ_Unknown"
        )
        assert isinstance(result, str)
        assert "Unsupported crop" in result

    def test_get_supported_crops_returns_list(self):
        crops = self.get_crops()
        assert isinstance(crops, list)
        assert len(crops) > 0
        assert "Rice, paddy" in crops

    def test_yield_unit_is_hg_ha(self):
        """Verify returned value is in hg/ha range (roughly 1000–100000 for staple crops)."""
        result = self.predict(
            year=2024, rainfall=1200, pesticides=100, temperature=25,
            crop_name="Wheat"
        )
        assert isinstance(result, float)
        assert 100 < result < 500_000, f"Yield {result} outside expected hg/ha range"


class TestConfig:
    """Smoke tests for the config module."""

    def test_crop_alias_is_dict(self):
        from ai_modules.yield_prediction.config import CROP_ALIAS
        assert isinstance(CROP_ALIAS, dict)

    def test_default_crop_list_not_empty(self):
        from ai_modules.yield_prediction.config import DEFAULT_CROP_LIST
        assert len(DEFAULT_CROP_LIST) > 0

    def test_data_dir_and_models_dir_exist(self):
        from ai_modules.yield_prediction.config import DATA_DIR, MODELS_DIR
        assert os.path.isdir(DATA_DIR),   f"data/ directory not found at {DATA_DIR}"
        assert os.path.isdir(MODELS_DIR), f"models/ directory not found at {MODELS_DIR}"

    def test_model_files_exist(self):
        from ai_modules.yield_prediction.config import MODELS_DIR
        assert os.path.isfile(os.path.join(MODELS_DIR, "yield_model.pkl"))
        assert os.path.isfile(os.path.join(MODELS_DIR, "crop_encoder.pkl"))


# ===========================================================================
# Integration Tests — require internet + API keys (mark to skip in CI)
# ===========================================================================

@pytest.mark.integration
class TestWeatherService:
    """Tests that hit the OpenWeather and Open-Meteo APIs."""

    def setup_method(self):
        from ai_modules.yield_prediction.weather_service import fetch_weather_data
        self.fetch = fetch_weather_data

    def test_valid_city_returns_temperature_and_humidity(self):
        result = self.fetch("Thanjavur")
        assert "error" not in result, f"API error: {result.get('error')}"
        assert result.get("temperature") is not None
        assert result.get("humidity") is not None

    def test_annual_rainfall_is_in_mm_year_range(self):
        """Annual rainfall should be in the 200–3000 mm range for Indian cities."""
        result = self.fetch("Thanjavur")
        if "error" not in result and result.get("rainfall") is not None:
            rainfall = result["rainfall"]
            assert 50 < rainfall < 5000, f"Rainfall {rainfall} mm outside plausible range"

    def test_invalid_city_returns_error_dict(self):
        result = self.fetch("NOTAREAL_CITY_XYZ_999")
        assert "error" in result


@pytest.mark.integration
class TestRecommendationPipeline:
    """Full end-to-end pipeline test."""

    LOCATIONS = [
        ("Tamil Nadu",  "Thanjavur"),
        ("Maharashtra", "Pune"),
        ("Punjab",      "Ludhiana"),
    ]
    CROPS = ["Rice, paddy", "Maize", "Wheat", "Potatoes"]

    @pytest.mark.parametrize("state,district", LOCATIONS)
    def test_run_forecast_returns_recommendations(self, state, district):
        from ai_modules.yield_prediction.revenue_forecast import run_forecast
        result = run_forecast(state=state, district=district, crop_list=self.CROPS)

        assert "recommended_crops" in result
        assert isinstance(result["recommended_crops"], list)
        assert len(result["recommended_crops"]) > 0, "Expected at least 1 recommendation"

        crop = result["recommended_crops"][0]
        assert "crop"             in crop
        assert "predicted_yield"  in crop
        assert "market_price"     in crop
        assert "expected_revenue" in crop
        assert "risk_level"       in crop

    def test_weather_key_in_response(self):
        from ai_modules.yield_prediction.revenue_forecast import run_forecast
        result = run_forecast("Tamil Nadu", "Thanjavur")
        assert "weather" in result
        assert "rainfall_mm"     in result["weather"]
        assert "rainfall_source" in result["weather"]
