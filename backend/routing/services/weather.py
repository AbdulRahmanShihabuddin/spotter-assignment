"""
Weather provider services for hourly checkpoint forecasts and caching.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
import logging
import math
import time
from typing import Any
import requests
from django.conf import settings
from routing.services.risk_engine import evaluate_checkpoint_weather

logger = logging.getLogger(__name__)

# In-memory weather cache: key = f"{lat_round}_{lon_round}", value = {"timestamp": time.time(), "hourly": [...]}
_WEATHER_CACHE: dict[str, dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _coord_cache_key(lat: float, lon: float) -> str:
    """Round coordinates to 2 decimal places (~1.1 km) for efficient cache reuse."""
    return f"{round(lat, 2)}_{round(lon, 2)}"


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse an ISO 8601 string to a timezone-aware UTC datetime."""
    # Strip trailing Z if present and parse
    clean_str = dt_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BaseWeatherProvider(ABC):
    @abstractmethod
    def enrich_checkpoints(
        self,
        checkpoints: list[dict[str, Any]],
        weight_lbs: float,
        departure_time: datetime
    ) -> list[dict[str, Any]]:
        """
        Enrich a list of checkpoints with weather forecast data and risk assessments.
        """
        pass


class OpenMeteoWeatherProvider(BaseWeatherProvider):
    """
    Open-Meteo weather provider with batching, hourly forecasts, and coordinate caching.
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, api_key: str | None = None, timeout: int = 20):
        self.api_key = api_key or getattr(settings, "OPENMETEO_API_KEY", "")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": getattr(settings, "GEOCODING_USER_AGENT", "spotter-weather-aware-truck-routing/1.0"),
            "Accept": "application/json",
        })

    def _fetch_batch_forecasts(self, coords: list[tuple[float, float]]) -> list[dict[str, Any] | None]:
        """
        Fetch hourly weather forecasts for a batch of coordinates.
        Uses 14-day forecast window + 1 past day to eliminate out-of-horizon mismatches.
        Returns list of parsed hourly forecast maps for each coordinate.
        """
        if not coords:
            return []

        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]

        params: dict[str, Any] = {
            "latitude": lats if len(lats) > 1 else lats[0],
            "longitude": lons if len(lons) > 1 else lons[0],
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "past_days": 1,
            "forecast_days": 14,
            "timezone": "UTC",
        }

        if self.api_key:
            params["apikey"] = self.api_key

        data = None
        for attempt in range(2):
            try:
                resp = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.RequestException as e:
                logger.warning("Open-Meteo batch request attempt %d failed: %s", attempt + 1, str(e))
                if attempt == 0:
                    time.sleep(0.5)

        if data is None:
            logger.error("Open-Meteo weather batch request failed after 2 attempts.")
            return [None] * len(coords)

        # Multi-location returns a list; single location returns an object
        raw_list = data if isinstance(data, list) else [data]
        results: list[dict[str, Any] | None] = []

        now_ts = time.time()
        for idx, item in enumerate(raw_list):
            if not item or "hourly" not in item:
                results.append(None)
                continue

            hourly = item.get("hourly", {})
            times = hourly.get("time", [])
            winds = hourly.get("wind_speed_10m", [])
            rains = hourly.get("rain", [])
            snows = hourly.get("snowfall", [])

            timeline = []
            for t_idx, time_str in enumerate(times):
                w = winds[t_idx] if t_idx < len(winds) else None
                r = rains[t_idx] if t_idx < len(rains) else None
                s = snows[t_idx] if t_idx < len(snows) else None
                timeline.append({
                    "time": time_str + "Z" if not time_str.endswith("Z") else time_str,
                    "wind_mph": float(w) if w is not None else None,
                    "rain_in_hr": float(r) if r is not None else None,
                    "snow_in_hr": float(s) if s is not None else None,
                })

            parsed = {"timeline": timeline}
            results.append(parsed)

            # Store in cache
            if idx < len(coords):
                c_key = _coord_cache_key(coords[idx][0], coords[idx][1])
                _WEATHER_CACHE[c_key] = {
                    "timestamp": now_ts,
                    "data": parsed
                }

        return results

    def _get_forecast_timeline_for_coord(self, lat: float, lon: float) -> list[dict[str, Any]] | None:
        """Lookup cached forecast timeline or return None if cache miss."""
        c_key = _coord_cache_key(lat, lon)
        entry = _WEATHER_CACHE.get(c_key)
        if entry and (time.time() - entry["timestamp"] < CACHE_TTL_SECONDS):
            return entry["data"].get("timeline")
        return None

    def enrich_checkpoints(
        self,
        checkpoints: list[dict[str, Any]],
        weight_lbs: float,
        departure_time: datetime
    ) -> list[dict[str, Any]]:
        if not checkpoints:
            return []

        # Find uncached coordinates that need fetching
        uncached_coords = []
        uncached_indices = []

        for idx, cp in enumerate(checkpoints):
            lat = cp["latitude"]
            lon = cp["longitude"]
            timeline = self._get_forecast_timeline_for_coord(lat, lon)
            if timeline is None:
                uncached_coords.append((lat, lon))
                uncached_indices.append(idx)

        # Batch fetch uncached coordinates in smaller chunks of 15 for reliability on cloud hosts
        chunk_size = 15
        for i in range(0, len(uncached_coords), chunk_size):
            chunk = uncached_coords[i:i + chunk_size]
            self._fetch_batch_forecasts(chunk)

        # Match each checkpoint's estimated arrival time to closest hourly forecast
        enriched = []
        for cp in checkpoints:
            lat = cp["latitude"]
            lon = cp["longitude"]
            timeline = self._get_forecast_timeline_for_coord(lat, lon)

            cp_copy = dict(cp)
            arrival_iso = cp.get("estimated_arrival_time")

            weather_at_arrival = None
            if timeline and arrival_iso:
                try:
                    arrival_dt = parse_iso_datetime(arrival_iso)
                    closest_entry = None
                    min_diff_sec = float("inf")

                    for entry in timeline:
                        f_dt = parse_iso_datetime(entry["time"])
                        diff_sec = abs((f_dt - arrival_dt).total_seconds())
                        if diff_sec < min_diff_sec:
                            min_diff_sec = diff_sec
                            closest_entry = entry

                    # Valid if within 90 minutes of an hourly forecast slot
                    if closest_entry and min_diff_sec <= 5400:
                        weather_at_arrival = {
                            "is_available": True,
                            "wind_mph": closest_entry["wind_mph"],
                            "rain_in_hr": closest_entry["rain_in_hr"],
                            "snow_in_hr": closest_entry["snow_in_hr"],
                            "forecast_time": closest_entry["time"],
                        }
                    else:
                        weather_at_arrival = {
                            "is_available": False,
                            "reason": "Arrival time outside available forecast horizon",
                        }
                except Exception as e:
                    logger.warning("Error matching arrival time for checkpoint: %s", str(e))
                    weather_at_arrival = {"is_available": False}
            else:
                weather_at_arrival = {"is_available": False}

            # Evaluate risk
            risk_data = evaluate_checkpoint_weather(weather_at_arrival, weight_lbs)
            cp_copy["weather"] = risk_data

            # Store compact 48-hour timeline for heatmap/slider use
            cp_copy["hourly_forecast"] = timeline[:48] if timeline else []
            enriched.append(cp_copy)

        return enriched


class MockWeatherProvider(BaseWeatherProvider):
    """
    Deterministic mock weather provider for unit tests and offline development.
    Simulates varied conditions along a corridor (moderate wind, localized rain/snow).
    """
    def enrich_checkpoints(
        self,
        checkpoints: list[dict[str, Any]],
        weight_lbs: float,
        departure_time: datetime
    ) -> list[dict[str, Any]]:
        enriched = []
        total_cp = len(checkpoints)

        for idx, cp in enumerate(checkpoints):
            cp_copy = dict(cp)
            arrival_iso = cp.get("estimated_arrival_time") or departure_time.isoformat()

            # Deterministic synthetic weather gradient across corridor sequence
            # E.g. mild start, moderate rain in middle, elevated wind near end
            progress = idx / max(total_cp - 1, 1)

            # Wind speed: 15 mph to 42 mph peak at 80% progress
            wind_mph = 15.0 + 26.0 * math.sin(progress * math.pi)

            # Rain intensity: localized shower around mid-route (progress ~ 0.4 - 0.7)
            rain_in_hr = 0.0
            if 0.35 <= progress <= 0.65:
                rain_in_hr = 0.28 * math.sin((progress - 0.35) / 0.30 * math.pi)

            # Snow intensity: 0.0 unless in northern/winter mock simulation
            snow_in_hr = 0.0

            weather_obs = {
                "is_available": True,
                "wind_mph": round(wind_mph, 1),
                "rain_in_hr": round(rain_in_hr, 3),
                "snow_in_hr": round(snow_in_hr, 3),
                "forecast_time": arrival_iso,
            }

            risk_data = evaluate_checkpoint_weather(weather_obs, weight_lbs)
            cp_copy["weather"] = risk_data

            # Generate synthetic 48-hour timeline for offline development / test slider inspection
            timeline = []
            base_dt = parse_iso_datetime(departure_time.isoformat() if isinstance(departure_time, datetime) else str(departure_time))
            for h in range(48):
                h_dt = base_dt + timedelta(hours=h)
                # Diurnal temperature/wind variation
                h_wind = max(5.0, wind_mph + 6.0 * math.sin((h + progress * 10) * 0.25))
                h_rain = max(0.0, rain_in_hr * (1.0 + 0.5 * math.cos(h * 0.3)))
                timeline.append({
                    "time": h_dt.isoformat(),
                    "wind_mph": round(h_wind, 1),
                    "rain_in_hr": round(h_rain, 3),
                    "snow_in_hr": 0.0,
                })

            cp_copy["hourly_forecast"] = timeline
            enriched.append(cp_copy)

        return enriched


def get_weather_provider() -> BaseWeatherProvider:
    """
    Factory returns the active weather provider based on settings.
    """
    use_mock = getattr(settings, "USE_MOCK_WEATHER", False)
    if use_mock:
        return MockWeatherProvider()

    provider_name = getattr(settings, "WEATHER_PROVIDER", "open-meteo").lower()
    if provider_name == "mock":
        return MockWeatherProvider()

    return OpenMeteoWeatherProvider()
