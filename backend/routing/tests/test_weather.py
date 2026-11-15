from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from django.test import TestCase
from routing.services.weather import (
    OpenMeteoWeatherProvider,
    MockWeatherProvider,
    _WEATHER_CACHE,
    parse_iso_datetime,
)
from routing.services.risk_engine import RiskLevel


class WeatherServiceTest(TestCase):
    def setUp(self):
        _WEATHER_CACHE.clear()
        self.checkpoints = [
            {
                "id": "cp_0",
                "sequence": 0,
                "latitude": 41.8781,
                "longitude": -87.6298,
                "distance_miles": 0.0,
                "distance_meters": 0.0,
                "estimated_elapsed_seconds": 0.0,
                "estimated_arrival_time": "2026-11-16T10:00:00Z",
            },
            {
                "id": "cp_1",
                "sequence": 1,
                "latitude": 41.5000,
                "longitude": -88.0000,
                "distance_miles": 25.0,
                "distance_meters": 40233.0,
                "estimated_elapsed_seconds": 1800.0,
                "estimated_arrival_time": "2026-11-16T10:30:00Z",
            },
        ]
        self.dep_time = datetime(2026, 11, 16, 10, 0, 0, tzinfo=timezone.utc)

    def test_mock_weather_provider(self):
        provider = MockWeatherProvider()
        enriched = provider.enrich_checkpoints(
            checkpoints=self.checkpoints,
            weight_lbs=42000.0,
            departure_time=self.dep_time
        )
        self.assertEqual(len(enriched), 2)
        for cp in enriched:
            self.assertIn("weather", cp)
            w = cp["weather"]
            self.assertTrue(w["is_available"])
            self.assertIsNotNone(w["wind_mph"])
            self.assertIsNotNone(w["rain_in_hr"])
            self.assertIn("risk_level", w)
            self.assertIn(w["risk_level"], [r.value for r in RiskLevel])

    @patch("requests.Session.get")
    def test_open_meteo_success_and_matching(self, mock_get):
        # Mock Open-Meteo response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "hourly": {
                    "time": ["2026-11-16T09:00", "2026-11-16T10:00", "2026-11-16T11:00"],
                    "wind_speed_10m": [22.0, 38.5, 29.0],
                    "rain": [0.0, 0.35, 0.05],
                    "snowfall": [0.0, 0.0, 0.0],
                }
            },
            {
                "hourly": {
                    "time": ["2026-11-16T09:00", "2026-11-16T10:00", "2026-11-16T11:00"],
                    "wind_speed_10m": [15.0, 20.0, 25.0],
                    "rain": [0.0, 0.0, 0.0],
                    "snowfall": [0.0, 0.0, 0.0],
                }
            }
        ]
        mock_get.return_value = mock_resp

        provider = OpenMeteoWeatherProvider()
        # cp_0 arrives at 10:00: wind 38.5 mph, rain 0.35 in/hr
        # With 42,000 lb load: wind 38.5 mph (>40k lb) triggers Severe risk!
        enriched = provider.enrich_checkpoints(
            checkpoints=self.checkpoints,
            weight_lbs=42000.0,
            departure_time=self.dep_time
        )
        self.assertEqual(len(enriched), 2)

        cp0_weather = enriched[0]["weather"]
        self.assertTrue(cp0_weather["is_available"])
        self.assertEqual(cp0_weather["wind_mph"], 38.5)
        self.assertEqual(cp0_weather["rain_in_hr"], 0.35)
        self.assertEqual(cp0_weather["forecast_time"], "2026-11-16T10:00Z")
        self.assertEqual(cp0_weather["wind_risk"], RiskLevel.SEVERE.value)
        self.assertEqual(cp0_weather["risk_level"], RiskLevel.SEVERE.value)

    @patch("requests.Session.get")
    def test_open_meteo_caching(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "hourly": {
                "time": ["2026-11-16T10:00"],
                "wind_speed_10m": [12.0],
                "rain": [0.0],
                "snowfall": [0.0],
            }
        }
        mock_get.return_value = mock_resp

        provider = OpenMeteoWeatherProvider()
        single_cp = [self.checkpoints[0]]

        # Call 1: uncached, should call API
        provider.enrich_checkpoints(single_cp, 35000.0, self.dep_time)
        self.assertEqual(mock_get.call_count, 1)

        # Call 2: cached, should NOT call API again
        provider.enrich_checkpoints(single_cp, 35000.0, self.dep_time)
        self.assertEqual(mock_get.call_count, 1)

    @patch("requests.Session.get")
    def test_arrival_time_outside_forecast_horizon(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "hourly": {
                "time": ["2026-11-16T10:00", "2026-11-16T11:00"],
                "wind_speed_10m": [10.0, 10.0],
                "rain": [0.0, 0.0],
                "snowfall": [0.0, 0.0],
            }
        }
        mock_get.return_value = mock_resp

        # Checkpoint arriving 5 days in the future
        future_cp = [{
            "id": "cp_future",
            "sequence": 0,
            "latitude": 41.8781,
            "longitude": -87.6298,
            "distance_miles": 0.0,
            "distance_meters": 0.0,
            "estimated_elapsed_seconds": 0.0,
            "estimated_arrival_time": "2026-11-25T10:00:00Z",
        }]

        provider = OpenMeteoWeatherProvider()
        enriched = provider.enrich_checkpoints(future_cp, 35000.0, self.dep_time)
        self.assertEqual(len(enriched), 1)
        w = enriched[0]["weather"]
        self.assertFalse(w["is_available"])
        self.assertEqual(w["risk_level"], RiskLevel.UNAVAILABLE.value)

    @patch("requests.Session.get")
    def test_weather_api_failure_handled_gracefully(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectTimeout("Connection timed out")

        provider = OpenMeteoWeatherProvider()
        enriched = provider.enrich_checkpoints(self.checkpoints, 35000.0, self.dep_time)
        self.assertEqual(len(enriched), 2)
        for cp in enriched:
            w = cp["weather"]
            self.assertFalse(w["is_available"])
            self.assertEqual(w["risk_level"], RiskLevel.UNAVAILABLE.value)
