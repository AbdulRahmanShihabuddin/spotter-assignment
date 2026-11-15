from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from routing.services.geocoding import GeocodedLocation


class RoutePlanViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertIn("routing_provider", response.data)

    def test_invalid_input_empty_payload(self):
        response = self.client.post("/api/routes/plan/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("details", response.data)
        self.assertIn("origin", response.data["details"])
        self.assertIn("destination", response.data["details"])

    def test_invalid_input_identical_locations(self):
        payload = {
            "origin": "Dallas, TX",
            "destination": "Dallas, TX",
            "checkpoint_interval_miles": 25,
            "weight_lbs": 35000,
        }
        response = self.client.post("/api/routes/plan/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("destination", response.data["details"])

    @override_settings(USE_MOCK_ROUTING=True, DEBUG=True)
    def test_successful_plan_with_mock_services(self):
        payload = {
            "origin": "Chicago, IL",
            "destination": "Dallas, TX",
            "departure_time": "2026-11-16T10:00:00Z",
            "weight_lbs": 38000,
            "checkpoint_interval_miles": 25,
        }
        response = self.client.post("/api/routes/plan/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["origin"]["name"], "Chicago, IL")
        self.assertEqual(data["destination"]["name"], "Dallas, TX")
        self.assertEqual(data["weight_lbs"], 38000)
        self.assertEqual(data["checkpoint_interval_miles"], 25)
        self.assertEqual(data["total_routes_found"], 3)
        self.assertEqual(len(data["routes"]), 3)

        first_route = data["routes"][0]
        self.assertIn("route_id", first_route)
        self.assertIn("geometry", first_route)
        self.assertEqual(first_route["geometry"]["type"], "LineString")
        self.assertGreater(len(first_route["geometry"]["coordinates"]), 0)
        self.assertGreater(len(first_route["checkpoints"]), 0)
        self.assertGreater(first_route["distance_miles"], 0)
        self.assertGreater(first_route["duration_hours"], 0)
        self.assertIn("max_risk_level", first_route)
        self.assertIn("risk_counts", first_route)

        first_cp = first_route["checkpoints"][0]
        self.assertIn("weather", first_cp)
        self.assertIn("risk_level", first_cp["weather"])

        # Phase 3 verifications
        self.assertIn("risk_summary", first_route)
        summary = first_route["risk_summary"]
        self.assertIn("severe_risk_miles", summary)
        self.assertIn("high_risk_miles", summary)
        self.assertIn("average_risk", summary)
        self.assertIn("has_no_travel", summary)

        self.assertIn("recommendation", data)
        rec = data["recommendation"]
        self.assertTrue(rec["has_recommendation"])
        self.assertIsNotNone(rec["recommended_route_id"])
        self.assertGreater(len(rec["reason"]), 0)

    @override_settings(USE_MOCK_ROUTING=False)
    @patch("routing.services.geocoding.PhotonGeocodingService.geocode")
    def test_origin_not_found(self, mock_geocode):
        from routing.exceptions import GeocodingNotFoundError
        mock_geocode.side_effect = GeocodingNotFoundError("Uncharted Nowhere")

        payload = {
            "origin": "Uncharted Nowhere",
            "destination": "Dallas, TX",
        }
        response = self.client.post("/api/routes/plan/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], "location_not_found")
