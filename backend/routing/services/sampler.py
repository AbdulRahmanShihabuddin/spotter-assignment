"""
Route checkpoint sampling service.
Samples discrete waypoints along a route polyline at specified mileage intervals (e.g. 10, 25, 50 miles).
"""
import math
from datetime import datetime, timedelta
from typing import Any

METERS_TO_MILES = 0.000621371
MILES_TO_METERS = 1609.344


def haversine_distance(coord1: list[float] | tuple[float, float], coord2: list[float] | tuple[float, float]) -> float:
    """
    Calculate great-circle distance between two points on Earth in meters.
    coord format: [lon, lat] or (lon, lat)
    """
    lon1, lat1 = coord1[0], coord1[1]
    lon2, lat2 = coord2[0], coord2[1]

    # Convert decimal degrees to radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    radius_earth_meters = 6371000.0  # Mean radius of Earth

    return radius_earth_meters * c


def interpolate_coordinate(
    coord1: list[float], coord2: list[float], fraction: float
) -> list[float]:
    """
    Linearly interpolate between two [lon, lat] coordinates given fraction in [0, 1].
    """
    lon = coord1[0] + (coord2[0] - coord1[0]) * fraction
    lat = coord1[1] + (coord2[1] - coord1[1]) * fraction
    return [round(lon, 6), round(lat, 6)]


def sample_route_checkpoints(
    coordinates: list[list[float]],
    interval_miles: float,
    total_duration_seconds: float,
    departure_time: datetime | None = None
) -> list[dict[str, Any]]:
    """
    Sample checkpoint waypoints along the route at regular distance intervals.
    Returns list of checkpoint dictionaries with coordinates, cumulative mileage, and ETA.
    """
    if not coordinates:
        return []

    interval_meters = interval_miles * MILES_TO_METERS
    base_time = departure_time or datetime.utcnow()

    # Pre-calculate segment lengths and total route length in meters
    segment_lengths: list[float] = []
    total_distance_meters = 0.0

    for i in range(len(coordinates) - 1):
        seg_dist = haversine_distance(coordinates[i], coordinates[i + 1])
        segment_lengths.append(seg_dist)
        total_distance_meters += seg_dist

    if total_distance_meters <= 0:
        return [{
            "id": "cp_0",
            "sequence": 0,
            "latitude": coordinates[0][1],
            "longitude": coordinates[0][0],
            "distance_miles": 0.0,
            "distance_meters": 0.0,
            "estimated_elapsed_seconds": 0.0,
            "estimated_arrival_time": base_time.isoformat(),
        }]

    # Average travel speed in meters per second for time interpolation
    avg_speed_mps = total_distance_meters / total_duration_seconds if total_duration_seconds > 0 else 25.0

    checkpoints: list[dict[str, Any]] = []

    # Checkpoint 0: Origin
    checkpoints.append({
        "id": "cp_0",
        "sequence": 0,
        "latitude": round(coordinates[0][1], 6),
        "longitude": round(coordinates[0][0], 6),
        "distance_miles": 0.0,
        "distance_meters": 0.0,
        "estimated_elapsed_seconds": 0.0,
        "estimated_arrival_time": base_time.isoformat(),
    })

    current_target_dist = interval_meters
    accumulated_dist = 0.0
    cp_seq = 1

    for i, seg_dist in enumerate(segment_lengths):
        seg_start = coordinates[i]
        seg_end = coordinates[i + 1]

        while accumulated_dist + seg_dist >= current_target_dist and current_target_dist < total_distance_meters:
            # Target lies inside this segment
            dist_into_seg = current_target_dist - accumulated_dist
            fraction = dist_into_seg / seg_dist if seg_dist > 0 else 0.0
            interp_pt = interpolate_coordinate(seg_start, seg_end, fraction)

            elapsed_secs = current_target_dist / avg_speed_mps
            eta = base_time + timedelta(seconds=elapsed_secs)

            checkpoints.append({
                "id": f"cp_{cp_seq}",
                "sequence": cp_seq,
                "latitude": interp_pt[1],
                "longitude": interp_pt[0],
                "distance_miles": round(current_target_dist * METERS_TO_MILES, 1),
                "distance_meters": round(current_target_dist, 1),
                "estimated_elapsed_seconds": round(elapsed_secs, 1),
                "estimated_arrival_time": eta.isoformat(),
            })

            cp_seq += 1
            current_target_dist += interval_meters

        accumulated_dist += seg_dist

    # Final Checkpoint: Destination
    dest_coord = coordinates[-1]
    final_miles = round(total_distance_meters * METERS_TO_MILES, 1)
    final_eta = base_time + timedelta(seconds=total_duration_seconds)

    # If the last regular checkpoint is not right on top of destination
    last_cp = checkpoints[-1]
    if (abs(last_cp["latitude"] - dest_coord[1]) > 0.001 or
            abs(last_cp["longitude"] - dest_coord[0]) > 0.001):
        checkpoints.append({
            "id": f"cp_{cp_seq}",
            "sequence": cp_seq,
            "latitude": round(dest_coord[1], 6),
            "longitude": round(dest_coord[0], 6),
            "distance_miles": final_miles,
            "distance_meters": round(total_distance_meters, 1),
            "estimated_elapsed_seconds": round(total_duration_seconds, 1),
            "estimated_arrival_time": final_eta.isoformat(),
        })

    return checkpoints
