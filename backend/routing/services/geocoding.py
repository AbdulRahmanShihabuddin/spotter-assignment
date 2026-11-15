"""
Geocoding service interfaces and implementations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import requests
from django.conf import settings
from routing.exceptions import GeocodingError, GeocodingNotFoundError

logger = logging.getLogger(__name__)

# Simple in-memory cache for repeated geocoding queries within the backend process
_GEOCODE_CACHE: dict[str, "GeocodedLocation"] = {}


@dataclass(frozen=True)
class GeocodedLocation:
    name: str
    lat: float
    lon: float
    display_name: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "display_name": self.display_name,
        }


class BaseGeocodingService(ABC):
    @abstractmethod
    def geocode(self, query: str) -> GeocodedLocation:
        """Resolve an address or place name to geographical coordinates."""
        pass


class PhotonGeocodingService(BaseGeocodingService):
    """
    Geocodes addresses using the Photon API (photon.komoot.io), which is backed
    by OpenStreetMap data without the strict shared-IP rate limits of Nominatim.
    """
    BASE_URL = "https://photon.komoot.io/api/"

    def __init__(self, user_agent: str | None = None, timeout: int = 10):
        self.user_agent = user_agent or getattr(
            settings, "GEOCODING_USER_AGENT", "spotter-weather-aware-truck-routing/1.0"
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })

    def geocode(self, query: str) -> GeocodedLocation:
        clean_query = query.strip()
        if not clean_query:
            raise GeocodingError("Location query cannot be empty.")

        cache_key = clean_query.lower()
        if cache_key in _GEOCODE_CACHE:
            return _GEOCODE_CACHE[cache_key]

        params = {
            "q": clean_query,
            "limit": 1,
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            logger.error("Geocoding request timed out for '%s'", clean_query)
            raise GeocodingError(f"Geocoding service timed out while looking up '{clean_query}'. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error("Geocoding request failed for '%s': %s", clean_query, str(e))
            raise GeocodingError(f"Unable to connect to geocoding service: {str(e)}")

        features = data.get("features", []) if isinstance(data, dict) else []
        if not features:
            raise GeocodingNotFoundError(clean_query)

        first_feature = features[0]
        try:
            geometry = first_feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            lon = float(coordinates[0])
            lat = float(coordinates[1])
            properties = first_feature.get("properties", {})
            name_parts = [
                properties.get("name"),
                properties.get("city"),
                properties.get("state"),
                properties.get("country"),
            ]
            display_parts = list(dict.fromkeys(p for p in name_parts if p))
            display_name = ", ".join(display_parts) if display_parts else clean_query
        except (IndexError, KeyError, ValueError, TypeError) as e:
            logger.error("Invalid coordinates in geocoding response: %s", str(e))
            raise GeocodingError(f"Invalid geocoding response received for '{clean_query}'.")

        result = GeocodedLocation(
            name=clean_query,
            lat=lat,
            lon=lon,
            display_name=display_name,
        )

        _GEOCODE_CACHE[cache_key] = result
        return result


def geocode_location(query: str) -> dict | None:
    """
    Direct helper to geocode a location query via Photon API.
    Returns {'lat': lat, 'lon': lon} or None if not found.
    """
    clean_query = query.strip()
    if not clean_query:
        return None

    user_agent = getattr(
        settings, "GEOCODING_USER_AGENT", "spotter-weather-aware-truck-routing/1.0"
    )
    resp = requests.get(
        "https://photon.komoot.io/api/",
        params={"q": clean_query, "limit": 1},
        headers={"User-Agent": user_agent, "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    features = resp.json().get("features", [])
    if not features:
        return None

    # GeoJSON returns [longitude, latitude]
    lon, lat = features[0]["geometry"]["coordinates"]
    return {"lat": lat, "lon": lon}


# Backward compatibility alias for Nominatim
NominatimGeocodingService = PhotonGeocodingService


class MockGeocodingService(BaseGeocodingService):
    """
    Mock geocoding service for deterministic unit testing and offline development.
    """
    KNOWN_LOCATIONS = {
        "chicago": (41.8781, -87.6298, "Chicago, Cook County, Illinois, United States"),
        "chicago, il": (41.8781, -87.6298, "Chicago, Cook County, Illinois, United States"),
        "dallas": (32.7767, -96.7970, "Dallas, Dallas County, Texas, United States"),
        "dallas, tx": (32.7767, -96.7970, "Dallas, Dallas County, Texas, United States"),
        "new york": (40.7128, -74.0060, "New York, United States"),
        "new york, ny": (40.7128, -74.0060, "New York, United States"),
        "los angeles": (34.0522, -118.2437, "Los Angeles, California, United States"),
        "los angeles, ca": (34.0522, -118.2437, "Los Angeles, California, United States"),
        "atlanta": (33.7490, -84.3880, "Atlanta, Fulton County, Georgia, United States"),
        "atlanta, ga": (33.7490, -84.3880, "Atlanta, Fulton County, Georgia, United States"),
        "denver": (39.7392, -104.9903, "Denver, Colorado, United States"),
        "denver, co": (39.7392, -104.9903, "Denver, Colorado, United States"),
        "seattle": (47.6062, -122.3321, "Seattle, King County, Washington, United States"),
        "seattle, wa": (47.6062, -122.3321, "Seattle, King County, Washington, United States"),
        "miami": (25.7617, -80.1918, "Miami, Miami-Dade County, Florida, United States"),
        "miami, fl": (25.7617, -80.1918, "Miami, Miami-Dade County, Florida, United States"),
    }

    def geocode(self, query: str) -> GeocodedLocation:
        clean_query = query.strip()
        if not clean_query:
            raise GeocodingError("Location query cannot be empty.")

        key = clean_query.lower()
        if key in self.KNOWN_LOCATIONS:
            lat, lon, display = self.KNOWN_LOCATIONS[key]
            return GeocodedLocation(name=clean_query, lat=lat, lon=lon, display_name=display)

        # Allow coordinate string like "41.8781, -87.6298"
        parts = clean_query.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return GeocodedLocation(
                    name=clean_query,
                    lat=lat,
                    lon=lon,
                    display_name=f"Coordinates ({lat:.4f}, {lon:.4f})"
                )
            except ValueError:
                pass

        raise GeocodingNotFoundError(clean_query)


def get_geocoding_service() -> BaseGeocodingService:
    """
    Factory returns the configured geocoding service.
    """
    if getattr(settings, "USE_MOCK_ROUTING", False) and getattr(settings, "DEBUG", False):
        return MockGeocodingService()
    return PhotonGeocodingService()
