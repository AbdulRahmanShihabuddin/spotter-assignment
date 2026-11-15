"""
Weather risk classification engine for commercial truck routing.
Evaluates wind, rain, and snow intensity against safety thresholds and truck load weight rules.
"""
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"
    NO_TRAVEL = "No Travel"
    UNAVAILABLE = "Unavailable"


RISK_SEVERITY_ORDER = {
    RiskLevel.LOW.value: 1,
    RiskLevel.MODERATE.value: 2,
    RiskLevel.HIGH.value: 3,
    RiskLevel.SEVERE.value: 4,
    RiskLevel.NO_TRAVEL.value: 5,
    RiskLevel.UNAVAILABLE.value: 0,
}


# Unit Conversion Helpers
def kmh_to_mph(kmh: float) -> float:
    """Convert kilometers per hour to miles per hour."""
    return kmh * 0.621371


def mps_to_mph(mps: float) -> float:
    """Convert meters per second to miles per hour."""
    return mps * 2.23694


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm * 0.0393701


def cm_to_inches(cm: float) -> float:
    """Convert centimeters to inches."""
    return cm * 0.393701


def classify_wind_risk(wind_mph: float | None, weight_lbs: float) -> str:
    """
    Classify wind risk incorporating load weight rules:
    Base wind thresholds:
      - Below 25 mph: Low
      - 25–34 mph: Moderate  [25, 35)
      - 35–44 mph: High      [35, 45)
      - 45–54 mph: Severe    [45, 55)
      - 55 mph or above: No Travel [55, +inf)

    Load-related wind rules:
      - Wind speed of 55 mph or above: No Travel for every load.
      - Wind speed of 45–below 55 mph with load above 30,000 lb: No Travel.
      - Wind speed of 35–below 45 mph with load above 40,000 lb: Severe.
    """
    if wind_mph is None:
        return RiskLevel.UNAVAILABLE.value

    if wind_mph < 0:
        raise ValueError("Wind speed cannot be negative.")

    # Rule 1: Wind speed >= 55 mph -> No Travel for all loads
    if wind_mph >= 55.0:
        return RiskLevel.NO_TRAVEL.value

    # Rule 2: Wind speed 45 - below 55 mph
    if wind_mph >= 45.0:
        if weight_lbs > 30000.0:
            return RiskLevel.NO_TRAVEL.value
        return RiskLevel.SEVERE.value

    # Rule 3: Wind speed 35 - below 45 mph
    if wind_mph >= 35.0:
        if weight_lbs > 40000.0:
            return RiskLevel.SEVERE.value
        return RiskLevel.HIGH.value

    # Wind speed 25 - below 35 mph
    if wind_mph >= 25.0:
        return RiskLevel.MODERATE.value

    # Below 25 mph
    return RiskLevel.LOW.value


def classify_rain_risk(rain_in_hr: float | None) -> str:
    """
    Classify rainfall intensity risk (inches per hour):
      - Below 0.10: Low
      - 0.10–below 0.25: Moderate [0.10, 0.25)
      - 0.25–below 0.50: High     [0.25, 0.50)
      - 0.50–1.00: Severe         [0.50, 1.00] (upper boundary inclusive)
      - Above 1.00: No Travel     (1.00, +inf)
    """
    if rain_in_hr is None:
        return RiskLevel.UNAVAILABLE.value

    if rain_in_hr < 0:
        raise ValueError("Rainfall intensity cannot be negative.")

    if rain_in_hr > 1.00:
        return RiskLevel.NO_TRAVEL.value
    elif rain_in_hr >= 0.50:
        return RiskLevel.SEVERE.value
    elif rain_in_hr >= 0.25:
        return RiskLevel.HIGH.value
    elif rain_in_hr >= 0.10:
        return RiskLevel.MODERATE.value
    else:
        return RiskLevel.LOW.value


def classify_snow_risk(snow_in_hr: float | None) -> str:
    """
    Classify snowfall intensity risk (inches per hour):
      - Below 0.5: Low
      - 0.5–below 1.0: Moderate [0.5, 1.0)
      - 1.0–below 2.0: High     [1.0, 2.0)
      - 2.0–3.0: Severe         [2.0, 3.0] (upper boundary inclusive)
      - Above 3.0: No Travel     (3.0, +inf)
    """
    if snow_in_hr is None:
        return RiskLevel.UNAVAILABLE.value

    if snow_in_hr < 0:
        raise ValueError("Snowfall intensity cannot be negative.")

    if snow_in_hr > 3.0:
        return RiskLevel.NO_TRAVEL.value
    elif snow_in_hr >= 2.0:
        return RiskLevel.SEVERE.value
    elif snow_in_hr >= 1.0:
        return RiskLevel.HIGH.value
    elif snow_in_hr >= 0.5:
        return RiskLevel.MODERATE.value
    else:
        return RiskLevel.LOW.value


def calculate_combined_risk(wind_risk: str, rain_risk: str, snow_risk: str) -> str:
    """
    Combine individual risks into a single overall risk:
    - Highest severity level wins.
    - No Travel overrides all.
    - If any data is Unavailable and all available data is Low/Moderate,
      the risk remains Unavailable to prevent false sense of safety.
    """
    risks = [wind_risk, rain_risk, snow_risk]

    # If any condition is No Travel, immediate No Travel
    if any(r == RiskLevel.NO_TRAVEL.value for r in risks):
        return RiskLevel.NO_TRAVEL.value

    # If any condition is Severe, immediate Severe
    if any(r == RiskLevel.SEVERE.value for r in risks):
        return RiskLevel.SEVERE.value

    # If any condition is High, immediate High
    if any(r == RiskLevel.HIGH.value for r in risks):
        return RiskLevel.HIGH.value

    # If some data is unavailable:
    # Missing data must never be classified as safe (Low).
    if any(r == RiskLevel.UNAVAILABLE.value for r in risks):
        # If at least one known factor was Moderate, we can flag as Moderate or Unavailable
        if any(r == RiskLevel.MODERATE.value for r in risks):
            return RiskLevel.MODERATE.value
        return RiskLevel.UNAVAILABLE.value

    if any(r == RiskLevel.MODERATE.value for r in risks):
        return RiskLevel.MODERATE.value

    return RiskLevel.LOW.value


def evaluate_checkpoint_weather(
    weather: dict[str, Any] | None,
    weight_lbs: float
) -> dict[str, Any]:
    """
    Given a weather observation/forecast dictionary and truck weight,
    calculates condition risks and final combined risk.
    """
    if not weather or not weather.get("is_available", False):
        return {
            "is_available": False,
            "wind_mph": None,
            "rain_in_hr": None,
            "snow_in_hr": None,
            "forecast_time": None,
            "wind_risk": RiskLevel.UNAVAILABLE.value,
            "rain_risk": RiskLevel.UNAVAILABLE.value,
            "snow_risk": RiskLevel.UNAVAILABLE.value,
            "risk_level": RiskLevel.UNAVAILABLE.value,
        }

    wind_mph = weather.get("wind_mph")
    rain_in_hr = weather.get("rain_in_hr")
    snow_in_hr = weather.get("snow_in_hr")
    forecast_time = weather.get("forecast_time")

    wind_risk = classify_wind_risk(wind_mph, weight_lbs)
    rain_risk = classify_rain_risk(rain_in_hr)
    snow_risk = classify_snow_risk(snow_in_hr)
    combined = calculate_combined_risk(wind_risk, rain_risk, snow_risk)

    return {
        "is_available": True,
        "wind_mph": round(wind_mph, 1) if wind_mph is not None else None,
        "rain_in_hr": round(rain_in_hr, 3) if rain_in_hr is not None else None,
        "snow_in_hr": round(snow_in_hr, 3) if snow_in_hr is not None else None,
        "forecast_time": forecast_time,
        "wind_risk": wind_risk,
        "rain_risk": rain_risk,
        "snow_risk": snow_risk,
        "risk_level": combined,
    }
