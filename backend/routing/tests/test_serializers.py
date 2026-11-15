from django.test import TestCase
from routing.serializers import RoutePlanRequestSerializer


class RoutePlanRequestSerializerTest(TestCase):
    def test_valid_payload(self):
        payload = {
            "origin": "Chicago, IL",
            "destination": "Dallas, TX",
            "departure_time": "2026-11-16T08:00:00Z",
            "weight_lbs": 42000,
            "checkpoint_interval_miles": 25,
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["origin"], "Chicago, IL")
        self.assertEqual(serializer.validated_data["destination"], "Dallas, TX")
        self.assertEqual(serializer.validated_data["weight_lbs"], 42000)
        self.assertEqual(serializer.validated_data["checkpoint_interval_miles"], 25)

    def test_missing_origin(self):
        payload = {
            "destination": "Dallas, TX",
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("origin", serializer.errors)

    def test_missing_destination(self):
        payload = {
            "origin": "Chicago, IL",
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("destination", serializer.errors)

    def test_identical_origin_and_destination(self):
        payload = {
            "origin": "Chicago, IL",
            "destination": "Chicago, IL",
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("destination", serializer.errors)

    def test_invalid_checkpoint_interval(self):
        payload = {
            "origin": "Chicago, IL",
            "destination": "Dallas, TX",
            "checkpoint_interval_miles": 15,  # Only 10, 25, 50 allowed
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("checkpoint_interval_miles", serializer.errors)

    def test_weight_boundaries(self):
        # Negative weight
        s1 = RoutePlanRequestSerializer(data={"origin": "A", "destination": "B", "weight_lbs": 0})
        self.assertFalse(s1.is_valid())
        self.assertIn("weight_lbs", s1.errors)

        # Exceeds max
        s2 = RoutePlanRequestSerializer(data={"origin": "A", "destination": "B", "weight_lbs": 150000})
        self.assertFalse(s2.is_valid())
        self.assertIn("weight_lbs", s2.errors)

    def test_default_values(self):
        payload = {
            "origin": "Chicago, IL",
            "destination": "Dallas, TX",
        }
        serializer = RoutePlanRequestSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["checkpoint_interval_miles"], 25)
        self.assertEqual(serializer.validated_data["weight_lbs"], 35000.0)
