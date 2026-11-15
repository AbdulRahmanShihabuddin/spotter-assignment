"""
Mock route generation for offline testing and deterministic development.
Only permitted when DEBUG=True and USE_MOCK_ROUTING=True.
"""
import math
from datetime import datetime
from typing import Any
from routing.services.geocoding import GeocodedLocation
from routing.services.sampler import haversine_distance, sample_route_checkpoints, METERS_TO_MILES


def generate_mock_polyline(
    origin: tuple[float, float],
    dest: tuple[float, float],
    curvature: float = 0.0,
    num_points: int = 50
) -> list[list[float]]:
    """
    Generate realistic route coordinates [lon, lat] with a slight curve/detour.
    origin: (lat, lon)
    dest: (lat, lon)
    """
    coords = []
    lat1, lon1 = origin
    lat2, lon2 = dest

    # Vector from origin to dest
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Perpendicular vector for curvature offset
    perp_lat = -dlon
    perp_lon = dlat
    length = math.sqrt(perp_lat**2 + perp_lon**2) or 1.0
    perp_lat /= length
    perp_lon /= length

    for i in range(num_points):
        t = i / (num_points - 1)
        # Base straight line
        base_lat = lat1 + t * dlat
        base_lon = lon1 + t * dlon

        # Parabolic arc offset for natural highway curve
        arc_offset = math.sin(t * math.pi) * curvature
        lat = base_lat + arc_offset * perp_lat
        lon = base_lon + arc_offset * perp_lon

        coords.append([round(lon, 6), round(lat, 6)])

    return coords


def create_mock_routes(
    origin: GeocodedLocation,
    dest: GeocodedLocation,
    departure_time: datetime,
    checkpoint_interval_miles: float
) -> list[dict[str, Any]]:
    """
    Produce 3 realistic distinct mock routes between origin and destination.
    """
    orig_pt = (origin.lat, origin.lon)
    dest_pt = (dest.lat, dest.lon)

    # Base direct distance
    direct_dist_meters = haversine_distance([origin.lon, origin.lat], [dest.lon, dest.lat])

    configs = [
        {
            "route_id": "mock_route_1",
            "name": "Primary Interstate Corridor",
            "curvature": 0.15,
            "dist_factor": 1.18,
            "speed_mph": 58.0,
        },
        {
            "route_id": "mock_route_2",
            "name": "Eastern Highway Alternative",
            "curvature": -0.35,
            "dist_factor": 1.29,
            "speed_mph": 54.0,
        },
        {
            "route_id": "mock_route_3",
            "name": "Western Bypass Route",
            "curvature": 0.45,
            "dist_factor": 1.36,
            "speed_mph": 52.0,
        },
    ]

    routes = []
    for cfg in configs:
        coords = generate_mock_polyline(orig_pt, dest_pt, curvature=cfg["curvature"], num_points=60)
        dist_meters = direct_dist_meters * cfg["dist_factor"]
        dist_miles = dist_meters * METERS_TO_MILES
        duration_hours = dist_miles / cfg["speed_mph"]
        duration_seconds = duration_hours * 3600.0

        checkpoints = sample_route_checkpoints(
            coordinates=coords,
            interval_miles=checkpoint_interval_miles,
            total_duration_seconds=duration_seconds,
            departure_time=departure_time
        )

        routes.append({
            "route_id": cfg["route_id"],
            "name": cfg["name"],
            "distance_meters": round(dist_meters, 1),
            "distance_miles": round(dist_miles, 1),
            "duration_seconds": round(duration_seconds, 1),
            "duration_hours": round(duration_hours, 2),
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "checkpoints": checkpoints,
            "checkpoint_count": len(checkpoints),
            "is_mock": True,
            "provider": "mock",
        })

    return routes
