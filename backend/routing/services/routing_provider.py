"""
Routing provider interfaces and implementations.
Integrates with OSRM, OpenRouteService, and a structured mock provider.
"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any
import requests
from django.conf import settings
from routing.exceptions import RoutingProviderError, NoRoutesFoundError
from routing.services.geocoding import GeocodedLocation
from routing.services.sampler import sample_route_checkpoints, METERS_TO_MILES
from routing.services.mock_data import create_mock_routes

logger = logging.getLogger(__name__)


class BaseRoutingProvider(ABC):
    @abstractmethod
    def get_routes(
        self,
        origin: GeocodedLocation,
        destination: GeocodedLocation,
        departure_time: datetime,
        checkpoint_interval_miles: float,
        weight_lbs: float
    ) -> list[dict[str, Any]]:
        """
        Request route alternatives from routing service.
        Returns a list of standardized route dictionaries.
        """
        pass


class OSRMProvider(BaseRoutingProvider):
    """
    Open Source Routing Machine (OSRM) provider.
    Connects to an OSRM instance (such as the public demo server or private deployment).
    """

    def __init__(self, base_url: str | None = None, timeout: int = 15):
        self.base_url = (base_url or getattr(settings, "OSRM_BASE_URL", "https://router.project-osrm.org")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": getattr(settings, "GEOCODING_USER_AGENT", "spotter-weather-aware-truck-routing/1.0"),
            "Accept": "application/json",
        })

    def get_routes(
        self,
        origin: GeocodedLocation,
        destination: GeocodedLocation,
        departure_time: datetime,
        checkpoint_interval_miles: float,
        weight_lbs: float
    ) -> list[dict[str, Any]]:
        # OSRM expects coordinates formatted as: {lon},{lat};{lon},{lat}
        coords_str = f"{origin.lon:.6f},{origin.lat:.6f};{destination.lon:.6f},{destination.lat:.6f}"
        url = f"{self.base_url}/route/v1/driving/{coords_str}"

        params = {
            "overview": "full",
            "geometries": "geojson",
            "alternatives": "3",  # Request up to 3 alternative paths
            "steps": "false",
            "annotations": "false",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            logger.error("OSRM routing request timed out for %s -> %s", origin.name, destination.name)
            raise RoutingProviderError(
                "The routing engine timed out calculating paths. Please retry.",
                provider="osrm"
            )
        except requests.exceptions.RequestException as e:
            logger.error("OSRM routing request failed: %s", str(e))
            raise RoutingProviderError(
                f"Routing provider communication failure: {str(e)}",
                provider="osrm"
            )

        code = data.get("code")
        if code != "Ok":
            logger.warning("OSRM returned non-Ok code: %s", code)
            if code == "NoRoute":
                raise NoRoutesFoundError(origin.name, destination.name)
            raise RoutingProviderError(
                f"Routing service returned status: {code}",
                provider="osrm"
            )

        raw_routes = data.get("routes", [])
        if not raw_routes:
            raise NoRoutesFoundError(origin.name, destination.name)

        # Standardize routes without fabricating artificial alternatives
        routes: list[dict[str, Any]] = []

        # Sort raw routes by duration (fastest first)
        raw_routes = sorted(raw_routes, key=lambda r: r.get("duration", 0))

        # Commercial truck travel adjustment factor based on load weight
        # Standard OSRM passenger car speeds are ~10-15% faster than regulated 80,000 lbs semi-trucks
        speed_factor = 0.90 if weight_lbs > 20000 else 0.95

        for idx, r in enumerate(raw_routes[:3]):
            route_num = idx + 1
            distance_meters = float(r.get("distance", 0.0))
            raw_duration_sec = float(r.get("duration", 0.0))

            # Adjust duration for heavy commercial vehicle profile
            duration_seconds = raw_duration_sec / speed_factor if speed_factor > 0 else raw_duration_sec
            distance_miles = distance_meters * METERS_TO_MILES
            duration_hours = duration_seconds / 3600.0

            geometry = r.get("geometry", {})
            coords = geometry.get("coordinates", [])

            # Route label / name
            legs = r.get("legs", [])
            summary = legs[0].get("summary", "") if legs else ""
            if summary:
                route_name = f"Route {route_num}: via {summary}"
            elif route_num == 1:
                route_name = "Route 1: Primary Highway"
            else:
                route_name = f"Route {route_num}: Alternative Corridor"

            checkpoints = sample_route_checkpoints(
                coordinates=coords,
                interval_miles=checkpoint_interval_miles,
                total_duration_seconds=duration_seconds,
                departure_time=departure_time
            )

            routes.append({
                "route_id": f"route_{route_num}",
                "name": route_name,
                "distance_meters": round(distance_meters, 1),
                "distance_miles": round(distance_miles, 1),
                "duration_seconds": round(duration_seconds, 1),
                "duration_hours": round(duration_hours, 2),
                "geometry": geometry,
                "checkpoints": checkpoints,
                "checkpoint_count": len(checkpoints),
                "is_mock": False,
                "provider": "osrm",
            })

        return routes


class OpenRouteServiceProvider(BaseRoutingProvider):
    """
    OpenRouteService provider supporting Heavy Goods Vehicle (driving-hgv) routing.
    Requires OPENROUTESERVICE_API_KEY environment variable.
    """
    BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"

    def __init__(self, api_key: str | None = None, timeout: int = 15):
        self.api_key = api_key or getattr(settings, "OPENROUTESERVICE_API_KEY", "")
        if not self.api_key:
            raise RoutingProviderError(
                "OPENROUTESERVICE_API_KEY is not configured.",
                provider="openrouteservice"
            )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, application/geo+json",
        })

    def get_routes(
        self,
        origin: GeocodedLocation,
        destination: GeocodedLocation,
        departure_time: datetime,
        checkpoint_interval_miles: float,
        weight_lbs: float
    ) -> list[dict[str, Any]]:
        body = {
            "coordinates": [
                [origin.lon, origin.lat],
                [destination.lon, destination.lat]
            ],
            "alternative_routes": {
                "target_count": 3,
                "weight_factor": 1.4,
                "share_factor": 0.6
            },
            "instructions": False,
        }

        try:
            response = self.session.post(self.BASE_URL, json=body, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            raise RoutingProviderError("OpenRouteService request timed out.", provider="openrouteservice")
        except requests.exceptions.RequestException as e:
            raise RoutingProviderError(f"OpenRouteService failure: {str(e)}", provider="openrouteservice")

        features = data.get("features", [])
        if not features:
            raise NoRoutesFoundError(origin.name, destination.name)

        routes: list[dict[str, Any]] = []
        for idx, feat in enumerate(features[:3]):
            route_num = idx + 1
            properties = feat.get("properties", {})
            summary = properties.get("summary", {})
            distance_meters = float(summary.get("distance", 0.0))
            duration_seconds = float(summary.get("duration", 0.0))
            distance_miles = distance_meters * METERS_TO_MILES
            duration_hours = duration_seconds / 3600.0

            geometry = feat.get("geometry", {})
            coords = geometry.get("coordinates", [])

            checkpoints = sample_route_checkpoints(
                coordinates=coords,
                interval_miles=checkpoint_interval_miles,
                total_duration_seconds=duration_seconds,
                departure_time=departure_time
            )

            routes.append({
                "route_id": f"route_{route_num}",
                "name": f"HGV Route {route_num}" + (" (Fastest)" if route_num == 1 else " (Alternative)"),
                "distance_meters": round(distance_meters, 1),
                "distance_miles": round(distance_miles, 1),
                "duration_seconds": round(duration_seconds, 1),
                "duration_hours": round(duration_hours, 2),
                "geometry": geometry,
                "checkpoints": checkpoints,
                "checkpoint_count": len(checkpoints),
                "is_mock": False,
                "provider": "openrouteservice",
            })

        return routes


class MockRoutingProvider(BaseRoutingProvider):
    """
    Mock routing provider for deterministic testing and offline development.
    """
    def get_routes(
        self,
        origin: GeocodedLocation,
        destination: GeocodedLocation,
        departure_time: datetime,
        checkpoint_interval_miles: float,
        weight_lbs: float
    ) -> list[dict[str, Any]]:
        return create_mock_routes(
            origin=origin,
            dest=destination,
            departure_time=departure_time,
            checkpoint_interval_miles=checkpoint_interval_miles
        )


def get_routing_provider() -> BaseRoutingProvider:
    """
    Factory to retrieve the active routing provider based on configuration.
    Strictly forbids mock data in production (when DEBUG=False).
    """
    use_mock = getattr(settings, "USE_MOCK_ROUTING", False)
    is_debug = getattr(settings, "DEBUG", False)

    if use_mock:
        if not is_debug:
            raise RoutingProviderError(
                "Mock routing is explicitly forbidden when DEBUG=False.",
                provider="mock",
                status_code=500
            )
        return MockRoutingProvider()

    provider_name = getattr(settings, "ROUTING_PROVIDER", "osrm").lower()
    if provider_name == "openrouteservice":
        return OpenRouteServiceProvider()
    elif provider_name == "mock":
        if not is_debug:
            raise RoutingProviderError(
                "Mock routing is explicitly forbidden when DEBUG=False.",
                provider="mock",
                status_code=500
            )
        return MockRoutingProvider()

    # Default provider: OSRM
    return OSRMProvider()
