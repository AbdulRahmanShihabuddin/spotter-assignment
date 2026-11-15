from datetime import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from routing.services.geocoding import GeocodedLocation
from routing.services.routing_provider import (
    OSRMProvider,
    MockRoutingProvider,
    get_routing_provider,
)
from routing.exceptions import RoutingProviderError, NoRoutesFoundError


class RoutingProviderTest(TestCase):
    def setUp(self):
        self.origin = GeocodedLocation("Chicago, IL", 41.8781, -87.6298, "Chicago, Cook County, IL")
        self.dest = GeocodedLocation("Dallas, TX", 32.7767, -96.7970, "Dallas, TX")
        self.dep_time = datetime(2026, 11, 16, 9, 0, 0)

    def test_mock_routing_provider(self):
        provider = MockRoutingProvider()
        routes = provider.get_routes(
            origin=self.origin,
            destination=self.dest,
            departure_time=self.dep_time,
            checkpoint_interval_miles=25,
            weight_lbs=40000
        )
        self.assertEqual(len(routes), 3)
        for r in routes:
            self.assertTrue(r["is_mock"])
            self.assertEqual(r["provider"], "mock")
            self.assertGreater(r["distance_miles"], 0)
            self.assertGreater(r["duration_hours"], 0)
            self.assertIn("geometry", r)
            self.assertEqual(r["geometry"]["type"], "LineString")
            self.assertGreater(len(r["checkpoints"]), 0)

    @patch("requests.Session.get")
    def test_osrm_provider_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 1500000.0,
                    "duration": 60000.0,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-87.6298, 41.8781],
                            [-92.0000, 37.0000],
                            [-96.7970, 32.7767],
                        ]
                    },
                    "legs": [{"summary": "I-55 S"}]
                },
                {
                    "distance": 1550000.0,
                    "duration": 63000.0,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-87.6298, 41.8781],
                            [-90.0000, 36.0000],
                            [-96.7970, 32.7767],
                        ]
                    },
                    "legs": [{"summary": "I-57 S, I-40 W"}]
                }
            ]
        }
        mock_get.return_value = mock_resp

        provider = OSRMProvider()
        routes = provider.get_routes(
            origin=self.origin,
            destination=self.dest,
            departure_time=self.dep_time,
            checkpoint_interval_miles=50,
            weight_lbs=35000
        )
        # Exactly 2 routes returned (does not fabricate a 3rd route when only 2 exist)
        self.assertEqual(len(routes), 2)
        self.assertFalse(routes[0]["is_mock"])
        self.assertEqual(routes[0]["provider"], "osrm")
        self.assertIn("via I-55 S", routes[0]["name"])

    @patch("requests.Session.get")
    def test_osrm_provider_no_route(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": "NoRoute",
            "routes": []
        }
        mock_get.return_value = mock_resp

        provider = OSRMProvider()
        with self.assertRaises(NoRoutesFoundError):
            provider.get_routes(
                origin=self.origin,
                destination=self.dest,
                departure_time=self.dep_time,
                checkpoint_interval_miles=25,
                weight_lbs=35000
            )

    @override_settings(USE_MOCK_ROUTING=True, DEBUG=False)
    def test_mock_routing_forbidden_in_production(self):
        with self.assertRaises(RoutingProviderError):
            get_routing_provider()
