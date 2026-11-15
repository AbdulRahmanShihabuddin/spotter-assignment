from django.test import TestCase
from routing.services.risk_engine import (
    RiskLevel,
    classify_wind_risk,
    classify_rain_risk,
    classify_snow_risk,
    calculate_combined_risk,
    evaluate_checkpoint_weather,
    kmh_to_mph,
    mps_to_mph,
    mm_to_inches,
    cm_to_inches,
)


class RiskEngineTest(TestCase):
    # ------------------ Wind Risk & Boundaries ------------------
    def test_wind_boundaries_standard_load(self):
        weight = 35000.0  # Standard weight

        # Below 25 mph -> Low
        self.assertEqual(classify_wind_risk(0.0, weight), RiskLevel.LOW.value)
        self.assertEqual(classify_wind_risk(24.9, weight), RiskLevel.LOW.value)

        # 25 to 34.9 mph -> Moderate
        self.assertEqual(classify_wind_risk(25.0, weight), RiskLevel.MODERATE.value)
        self.assertEqual(classify_wind_risk(34.9, weight), RiskLevel.MODERATE.value)

        # 35 to 44.9 mph with 35k lb (<= 40k lb) -> High
        self.assertEqual(classify_wind_risk(35.0, weight), RiskLevel.HIGH.value)
        self.assertEqual(classify_wind_risk(44.9, weight), RiskLevel.HIGH.value)

        # 45 to 54.9 mph with 35k lb (> 30k lb) -> No Travel (due to load rule)
        self.assertEqual(classify_wind_risk(45.0, weight), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_wind_risk(54.9, weight), RiskLevel.NO_TRAVEL.value)

        # 55 mph or above -> No Travel
        self.assertEqual(classify_wind_risk(55.0, weight), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_wind_risk(75.0, weight), RiskLevel.NO_TRAVEL.value)

    # ------------------ Load-Related Wind Rules ------------------
    def test_load_rule_1_any_load_above_55mph(self):
        # Wind >= 55 mph -> No Travel for all loads
        for w in [5000.0, 25000.0, 30000.0, 45000.0, 80000.0]:
            self.assertEqual(classify_wind_risk(55.0, w), RiskLevel.NO_TRAVEL.value)
            self.assertEqual(classify_wind_risk(65.0, w), RiskLevel.NO_TRAVEL.value)

    def test_load_rule_2_wind_45_to_55mph(self):
        # 45 to below 55 mph:
        # Load <= 30,000 lb -> Severe
        self.assertEqual(classify_wind_risk(45.0, 25000.0), RiskLevel.SEVERE.value)
        self.assertEqual(classify_wind_risk(54.9, 30000.0), RiskLevel.SEVERE.value)

        # Load > 30,000 lb -> No Travel
        self.assertEqual(classify_wind_risk(45.0, 30001.0), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_wind_risk(50.0, 45000.0), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_wind_risk(54.9, 80000.0), RiskLevel.NO_TRAVEL.value)

    def test_load_rule_3_wind_35_to_45mph(self):
        # 35 to below 45 mph:
        # Load <= 40,000 lb -> High
        self.assertEqual(classify_wind_risk(35.0, 20000.0), RiskLevel.HIGH.value)
        self.assertEqual(classify_wind_risk(44.9, 40000.0), RiskLevel.HIGH.value)

        # Load > 40,000 lb -> Severe
        self.assertEqual(classify_wind_risk(35.0, 40001.0), RiskLevel.SEVERE.value)
        self.assertEqual(classify_wind_risk(40.0, 65000.0), RiskLevel.SEVERE.value)
        self.assertEqual(classify_wind_risk(44.9, 80000.0), RiskLevel.SEVERE.value)

    # ------------------ Rain Risk & Boundaries ------------------
    def test_rain_boundaries(self):
        # Below 0.10 -> Low
        self.assertEqual(classify_rain_risk(0.0), RiskLevel.LOW.value)
        self.assertEqual(classify_rain_risk(0.099), RiskLevel.LOW.value)

        # 0.10 to below 0.25 -> Moderate
        self.assertEqual(classify_rain_risk(0.10), RiskLevel.MODERATE.value)
        self.assertEqual(classify_rain_risk(0.249), RiskLevel.MODERATE.value)

        # 0.25 to below 0.50 -> High
        self.assertEqual(classify_rain_risk(0.25), RiskLevel.HIGH.value)
        self.assertEqual(classify_rain_risk(0.499), RiskLevel.HIGH.value)

        # 0.50 to 1.00 (inclusive) -> Severe
        self.assertEqual(classify_rain_risk(0.50), RiskLevel.SEVERE.value)
        self.assertEqual(classify_rain_risk(0.75), RiskLevel.SEVERE.value)
        self.assertEqual(classify_rain_risk(1.00), RiskLevel.SEVERE.value)

        # Above 1.00 -> No Travel
        self.assertEqual(classify_rain_risk(1.001), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_rain_risk(2.50), RiskLevel.NO_TRAVEL.value)

    # ------------------ Snow Risk & Boundaries ------------------
    def test_snow_boundaries(self):
        # Below 0.5 -> Low
        self.assertEqual(classify_snow_risk(0.0), RiskLevel.LOW.value)
        self.assertEqual(classify_snow_risk(0.49), RiskLevel.LOW.value)

        # 0.5 to below 1.0 -> Moderate
        self.assertEqual(classify_snow_risk(0.50), RiskLevel.MODERATE.value)
        self.assertEqual(classify_snow_risk(0.99), RiskLevel.MODERATE.value)

        # 1.0 to below 2.0 -> High
        self.assertEqual(classify_snow_risk(1.00), RiskLevel.HIGH.value)
        self.assertEqual(classify_snow_risk(1.99), RiskLevel.HIGH.value)

        # 2.0 to 3.0 (inclusive) -> Severe
        self.assertEqual(classify_snow_risk(2.00), RiskLevel.SEVERE.value)
        self.assertEqual(classify_snow_risk(2.50), RiskLevel.SEVERE.value)
        self.assertEqual(classify_snow_risk(3.00), RiskLevel.SEVERE.value)

        # Above 3.0 -> No Travel
        self.assertEqual(classify_snow_risk(3.01), RiskLevel.NO_TRAVEL.value)
        self.assertEqual(classify_snow_risk(5.00), RiskLevel.NO_TRAVEL.value)

    # ------------------ Combined Weather Risk ------------------
    def test_combined_risk(self):
        # All low -> Low
        self.assertEqual(
            calculate_combined_risk("Low", "Low", "Low"),
            RiskLevel.LOW.value
        )

        # Moderate overrides Low
        self.assertEqual(
            calculate_combined_risk("Low", "Moderate", "Low"),
            RiskLevel.MODERATE.value
        )

        # High overrides Moderate and Low
        self.assertEqual(
            calculate_combined_risk("High", "Moderate", "Low"),
            RiskLevel.HIGH.value
        )

        # Severe overrides High
        self.assertEqual(
            calculate_combined_risk("High", "Severe", "Low"),
            RiskLevel.SEVERE.value
        )

        # No Travel overrides everything
        self.assertEqual(
            calculate_combined_risk("Low", "No Travel", "Low"),
            RiskLevel.NO_TRAVEL.value
        )
        self.assertEqual(
            calculate_combined_risk("Severe", "No Travel", "High"),
            RiskLevel.NO_TRAVEL.value
        )

    # ------------------ Missing / Unavailable Data ------------------
    def test_missing_data_never_classified_as_low(self):
        # Missing wind
        self.assertEqual(classify_wind_risk(None, 40000), RiskLevel.UNAVAILABLE.value)
        # Missing rain
        self.assertEqual(classify_rain_risk(None), RiskLevel.UNAVAILABLE.value)
        # Missing snow
        self.assertEqual(classify_snow_risk(None), RiskLevel.UNAVAILABLE.value)

        # Combined when all are unavailable
        self.assertEqual(
            calculate_combined_risk("Unavailable", "Unavailable", "Unavailable"),
            RiskLevel.UNAVAILABLE.value
        )

        # Combined when two are Low and one is Unavailable -> NEVER Low
        result = calculate_combined_risk("Low", "Low", "Unavailable")
        self.assertNotEqual(result, RiskLevel.LOW.value)
        self.assertEqual(result, RiskLevel.UNAVAILABLE.value)

        # Severe or No Travel still takes precedence even if one field is unavailable
        self.assertEqual(
            calculate_combined_risk("Severe", "Low", "Unavailable"),
            RiskLevel.SEVERE.value
        )
        self.assertEqual(
            calculate_combined_risk("No Travel", "Low", "Unavailable"),
            RiskLevel.NO_TRAVEL.value
        )

    def test_evaluate_checkpoint_weather(self):
        # Available weather with moderate wind, low rain/snow
        weather = {
            "is_available": True,
            "wind_mph": 28.0,
            "rain_in_hr": 0.02,
            "snow_in_hr": 0.0,
            "forecast_time": "2026-11-16T10:00:00Z"
        }
        res = evaluate_checkpoint_weather(weather, weight_lbs=35000.0)
        self.assertTrue(res["is_available"])
        self.assertEqual(res["wind_risk"], RiskLevel.MODERATE.value)
        self.assertEqual(res["rain_risk"], RiskLevel.LOW.value)
        self.assertEqual(res["snow_risk"], RiskLevel.LOW.value)
        self.assertEqual(res["risk_level"], RiskLevel.MODERATE.value)

        # Unavailable weather object
        unavail_res = evaluate_checkpoint_weather(None, weight_lbs=35000.0)
        self.assertFalse(unavail_res["is_available"])
        self.assertEqual(unavail_res["risk_level"], RiskLevel.UNAVAILABLE.value)

    # ------------------ Unit Conversions ------------------
    def test_unit_conversions(self):
        self.assertAlmostEqual(kmh_to_mph(100.0), 62.1371, places=3)
        self.assertAlmostEqual(mps_to_mph(10.0), 22.3694, places=3)
        self.assertAlmostEqual(mm_to_inches(25.4), 1.0, places=3)
        self.assertAlmostEqual(cm_to_inches(2.54), 1.0, places=3)
