"""
Unit and integration tests for route risk summaries and recommendation engine.
Verifies lexicographical ranking priorities, No Travel handling, and deterministic explanations.
"""
from django.test import TestCase
from routing.services.risk_engine import RiskLevel
from routing.services.recommendation import (
    calculate_route_risk_summary,
    rank_and_recommend_routes,
    _worse_risk,
)


class TestRouteRiskSummary(TestCase):
    def test_worse_risk_logic(self):
        """Test conservative worse-of-two endpoint rule."""
        self.assertEqual(_worse_risk(RiskLevel.LOW.value, RiskLevel.LOW.value), RiskLevel.LOW.value)
        self.assertEqual(_worse_risk(RiskLevel.LOW.value, RiskLevel.MODERATE.value), RiskLevel.MODERATE.value)
        self.assertEqual(_worse_risk(RiskLevel.MODERATE.value, RiskLevel.HIGH.value), RiskLevel.HIGH.value)
        self.assertEqual(_worse_risk(RiskLevel.LOW.value, RiskLevel.SEVERE.value), RiskLevel.SEVERE.value)
        self.assertEqual(_worse_risk(RiskLevel.SEVERE.value, RiskLevel.NO_TRAVEL.value), RiskLevel.NO_TRAVEL.value)
        # Unavailable with Low remains Unavailable (never silently Low)
        self.assertEqual(_worse_risk(RiskLevel.LOW.value, RiskLevel.UNAVAILABLE.value), RiskLevel.UNAVAILABLE.value)
        # Severe overrides Unavailable in hazard terms
        self.assertEqual(_worse_risk(RiskLevel.SEVERE.value, RiskLevel.UNAVAILABLE.value), RiskLevel.SEVERE.value)

    def test_calculate_risk_summary_multi_segment(self):
        """Test segment mileage and distance-weighted average risk calculation."""
        # 3 checkpoints: 0 mi (Low), 25 mi (Moderate), 50 mi (Severe)
        # Segment 1: [0 -> 25 mi, 25 miles], worse risk = Moderate (score 1.0)
        # Segment 2: [25 -> 50 mi, 25 miles], worse risk = Severe (score 3.0)
        checkpoints = [
            {"distance_miles": 0.0, "weather": {"risk_level": RiskLevel.LOW.value}},
            {"distance_miles": 25.0, "weather": {"risk_level": RiskLevel.MODERATE.value}},
            {"distance_miles": 50.0, "weather": {"risk_level": RiskLevel.SEVERE.value}},
        ]

        summary = calculate_route_risk_summary(
            checkpoints=checkpoints,
            total_distance_miles=50.0,
            travel_duration_hours=1.0
        )

        self.assertEqual(summary["total_distance_miles"], 50.0)
        self.assertEqual(summary["travel_duration_hours"], 1.0)
        self.assertEqual(summary["low_risk_miles"], 0.0)
        self.assertEqual(summary["moderate_risk_miles"], 25.0)
        self.assertEqual(summary["high_risk_miles"], 0.0)
        self.assertEqual(summary["severe_risk_miles"], 25.0)
        self.assertEqual(summary["no_travel_miles"], 0.0)
        self.assertFalse(summary["has_no_travel"])
        self.assertFalse(summary["has_unavailable"])

        # Average risk: (25 * 1.0 + 25 * 3.0) / 50 = (25 + 75) / 50 = 2.0
        self.assertAlmostEqual(summary["average_risk"], 2.0, places=2)

    def test_calculate_risk_summary_no_travel_exposure(self):
        """Route crossing a No Travel point must flag has_no_travel = True."""
        checkpoints = [
            {"distance_miles": 0.0, "weather": {"risk_level": RiskLevel.LOW.value}},
            {"distance_miles": 30.0, "weather": {"risk_level": RiskLevel.NO_TRAVEL.value}},
        ]
        summary = calculate_route_risk_summary(checkpoints, 30.0, 0.7)
        self.assertTrue(summary["has_no_travel"])
        self.assertEqual(summary["no_travel_miles"], 30.0)

    def test_calculate_risk_summary_unavailable_exposure(self):
        """Route with unavailable forecast must flag has_unavailable = True."""
        checkpoints = [
            {"distance_miles": 0.0, "weather": {"risk_level": RiskLevel.LOW.value}},
            {"distance_miles": 20.0, "weather": {"risk_level": RiskLevel.UNAVAILABLE.value}},
        ]
        summary = calculate_route_risk_summary(checkpoints, 20.0, 0.5)
        self.assertTrue(summary["has_unavailable"])
        self.assertEqual(summary["unavailable_miles"], 20.0)


class TestRouteRecommendationEngine(TestCase):
    def test_priority_1_fewest_severe_miles(self):
        """Priority 1: Route with fewest Severe miles wins even if longer."""
        routes = [
            {
                "route_id": "route_A",
                "name": "Route A",
                "duration_seconds": 3600,  # 1 hr
                "risk_summary": {
                    "severe_risk_miles": 15.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 1.2,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_B",
                "name": "Route B",
                "duration_seconds": 4500,  # 1.25 hrs (longer, but zero severe)
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 10.0,
                    "average_risk": 0.8,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertTrue(result["has_recommendation"])
        self.assertEqual(result["recommended_route_id"], "route_B")
        self.assertIn("severe-risk miles", result["reason"].lower())

    def test_priority_2_fewest_high_miles(self):
        """Priority 2: Equal Severe miles (0), fewest High miles wins."""
        routes = [
            {
                "route_id": "route_A",
                "name": "Route A",
                "duration_seconds": 3600,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 20.0,
                    "average_risk": 1.1,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_B",
                "name": "Route B",
                "duration_seconds": 4000,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 5.0,
                    "average_risk": 0.6,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertTrue(result["has_recommendation"])
        self.assertEqual(result["recommended_route_id"], "route_B")
        self.assertIn("high-risk exposure", result["reason"].lower())

    def test_priority_3_lowest_average_risk(self):
        """Priority 3: Equal Severe and High miles (0), lowest average risk wins."""
        routes = [
            {
                "route_id": "route_A",
                "name": "Route A",
                "duration_seconds": 3600,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.75,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_B",
                "name": "Route B",
                "duration_seconds": 3800,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.20,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertTrue(result["has_recommendation"])
        self.assertEqual(result["recommended_route_id"], "route_B")
        self.assertIn("lowest average weather risk", result["reason"].lower())

    def test_priority_4_shortest_travel_time(self):
        """Priority 4: Equal safety risk profiles, shortest travel time wins."""
        routes = [
            {
                "route_id": "route_A",
                "name": "Route A",
                "duration_seconds": 5400,  # 1h 30m
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.10,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_B",
                "name": "Route B",
                "duration_seconds": 4200,  # 1h 10m (faster)
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.10,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertTrue(result["has_recommendation"])
        self.assertEqual(result["recommended_route_id"], "route_B")
        self.assertIn("shortest travel time", result["reason"].lower())

    def test_no_travel_exclusion(self):
        """Route with No Travel must be marked ineligible and NOT recommended."""
        routes = [
            {
                "route_id": "route_fast_hazardous",
                "name": "Fast but No Travel",
                "duration_seconds": 1800,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.0,
                    "has_no_travel": True,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_safe_longer",
                "name": "Safe Longer Route",
                "duration_seconds": 7200,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 5.0,
                    "average_risk": 0.4,
                    "has_no_travel": False,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertTrue(result["has_recommendation"])
        self.assertEqual(result["recommended_route_id"], "route_safe_longer")
        self.assertFalse(routes[0]["is_eligible"])
        self.assertTrue(routes[1]["is_eligible"])

    def test_unavailable_data_exclusion(self):
        """Route with unavailable weather data must not silently be treated as safe."""
        routes = [
            {
                "route_id": "route_unavail",
                "name": "Missing Weather Route",
                "duration_seconds": 1800,
                "risk_summary": {
                    "severe_risk_miles": 0.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 0.0,
                    "has_no_travel": False,
                    "has_unavailable": True,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertFalse(result["has_recommendation"])
        self.assertIsNone(result["recommended_route_id"])
        self.assertIn("unavailable", result["reason"].lower())

    def test_all_routes_ineligible_no_travel(self):
        """When all routes contain No Travel, engine clearly reports no safe recommendation."""
        routes = [
            {
                "route_id": "route_1",
                "name": "Route 1",
                "duration_seconds": 3600,
                "risk_summary": {
                    "severe_risk_miles": 10.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 2.5,
                    "has_no_travel": True,
                    "has_unavailable": False,
                }
            },
            {
                "route_id": "route_2",
                "name": "Route 2",
                "duration_seconds": 4000,
                "risk_summary": {
                    "severe_risk_miles": 5.0,
                    "high_risk_miles": 0.0,
                    "average_risk": 2.0,
                    "has_no_travel": True,
                    "has_unavailable": False,
                }
            }
        ]

        result = rank_and_recommend_routes(routes)
        self.assertFalse(result["has_recommendation"])
        self.assertIsNone(result["recommended_route_id"])
        self.assertIn("no safe corridor recommendation available", result["reason"].lower())
        self.assertIn("no travel", result["reason"].lower())

    def test_determinism_same_input(self):
        """Verifies that the same input produces the exact same recommendation."""
        routes = [
            {
                "route_id": "route_1",
                "duration_seconds": 5000,
                "risk_summary": {"severe_risk_miles": 0.0, "high_risk_miles": 10.0, "average_risk": 0.5, "has_no_travel": False, "has_unavailable": False}
            },
            {
                "route_id": "route_2",
                "duration_seconds": 4500,
                "risk_summary": {"severe_risk_miles": 0.0, "high_risk_miles": 10.0, "average_risk": 0.5, "has_no_travel": False, "has_unavailable": False}
            }
        ]

        import copy
        res1 = rank_and_recommend_routes(copy.deepcopy(routes))
        res2 = rank_and_recommend_routes(copy.deepcopy(routes))

        self.assertEqual(res1["recommended_route_id"], res2["recommended_route_id"])
        self.assertEqual(res1["reason"], res2["reason"])
