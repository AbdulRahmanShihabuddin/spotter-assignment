from datetime import datetime
from django.test import TestCase
from routing.services.sampler import (
    haversine_distance,
    sample_route_checkpoints,
    interpolate_coordinate,
    MILES_TO_METERS,
)


class SamplerTest(TestCase):
    def test_haversine_distance(self):
        # Known distance between Chicago (-87.6298, 41.8781) and Dallas (-96.7970, 32.7767)
        # Approximate great circle distance is ~1290 km (~800 miles)
        dist = haversine_distance([-87.6298, 41.8781], [-96.7970, 32.7767])
        self.assertGreater(dist, 1200000)
        self.assertLess(dist, 1400000)

    def test_interpolate_coordinate(self):
        p1 = [0.0, 0.0]
        p2 = [10.0, 20.0]
        mid = interpolate_coordinate(p1, p2, 0.5)
        self.assertEqual(mid, [5.0, 10.0])

    def test_sample_route_checkpoints(self):
        # Straight line path of approximately 100 miles
        # 1 degree latitude ~ 69 miles
        # From (0, 0) to (0, 1.45) ~ 100 miles
        coords = [
            [0.0, 0.0],
            [0.0, 0.725],
            [0.0, 1.45],
        ]
        dep_time = datetime(2026, 11, 16, 8, 0, 0)
        total_duration = 7200.0  # 2 hours

        checkpoints = sample_route_checkpoints(
            coordinates=coords,
            interval_miles=25,
            total_duration_seconds=total_duration,
            departure_time=dep_time
        )

        # Checkpoints should include cp_0 (origin), cp_1 (~25mi), cp_2 (~50mi), cp_3 (~75mi), cp_4 (dest)
        self.assertGreaterEqual(len(checkpoints), 4)
        self.assertEqual(checkpoints[0]["sequence"], 0)
        self.assertEqual(checkpoints[0]["distance_miles"], 0.0)
        self.assertEqual(checkpoints[0]["id"], "cp_0")

        # Monotonically increasing distances
        for i in range(len(checkpoints) - 1):
            self.assertLess(checkpoints[i]["distance_miles"], checkpoints[i + 1]["distance_miles"])
            self.assertLess(checkpoints[i]["estimated_elapsed_seconds"], checkpoints[i + 1]["estimated_elapsed_seconds"])

        # Final checkpoint should match dest coordinates
        self.assertAlmostEqual(checkpoints[-1]["latitude"], 1.45, places=3)
        self.assertAlmostEqual(checkpoints[-1]["longitude"], 0.0, places=3)

    def test_sample_empty_coordinates(self):
        checkpoints = sample_route_checkpoints([], 25, 3600)
        self.assertEqual(checkpoints, [])
