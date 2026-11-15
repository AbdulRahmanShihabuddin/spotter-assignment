"""
Route risk summaries and deterministic route recommendation engine.
Implements distance-weighted segment risk calculations and lexicographic route ranking.
"""
from typing import Any
from routing.services.risk_engine import (
    RiskLevel,
    RISK_SEVERITY_ORDER,
)

# Ordered numerical scale for average risk calculation as specified in the assignment:
# Low: 0, Moderate: 1, High: 2, Severe: 3, No Travel: 4
RISK_NUMERICAL_SCALE: dict[str, float] = {
    RiskLevel.LOW.value: 0.0,
    RiskLevel.MODERATE.value: 1.0,
    RiskLevel.HIGH.value: 2.0,
    RiskLevel.SEVERE.value: 3.0,
    RiskLevel.NO_TRAVEL.value: 4.0,
}


def _worse_risk(risk_a: str, risk_b: str) -> str:
    """
    Returns the worse (higher severity) of two risk classifications.
    Conservative segment risk rule: assign each segment between adjacent checkpoints
    the worse of the two endpoint risk classifications.
    """
    # If either is No Travel, segment is No Travel
    if risk_a == RiskLevel.NO_TRAVEL.value or risk_b == RiskLevel.NO_TRAVEL.value:
        return RiskLevel.NO_TRAVEL.value

    # If either is Severe, segment is Severe
    if risk_a == RiskLevel.SEVERE.value or risk_b == RiskLevel.SEVERE.value:
        return RiskLevel.SEVERE.value

    # If either is High, segment is High
    if risk_a == RiskLevel.HIGH.value or risk_b == RiskLevel.HIGH.value:
        return RiskLevel.HIGH.value

    # If either is Moderate, segment is Moderate
    if risk_a == RiskLevel.MODERATE.value or risk_b == RiskLevel.MODERATE.value:
        return RiskLevel.MODERATE.value

    # If either is Unavailable and the other is Low, segment is Unavailable
    # (Missing data must never be treated as safe)
    if risk_a == RiskLevel.UNAVAILABLE.value or risk_b == RiskLevel.UNAVAILABLE.value:
        return RiskLevel.UNAVAILABLE.value

    return RiskLevel.LOW.value


def calculate_route_risk_summary(
    checkpoints: list[dict[str, Any]],
    total_distance_miles: float,
    travel_duration_hours: float
) -> dict[str, Any]:
    """
    Calculates distance-weighted risk exposure for a route based on checkpoint weather at ETA:
    - Severe-risk miles
    - High-risk miles
    - Moderate-risk miles
    - Low-risk miles
    - No Travel miles and exposure flag
    - Unavailable miles and exposure flag
    - Average risk (0.0 to 3.0+ scale, weighted by segment distance)
    - Total distance and travel duration
    """
    if not checkpoints:
        return {
            "severe_risk_miles": 0.0,
            "high_risk_miles": 0.0,
            "moderate_risk_miles": 0.0,
            "low_risk_miles": 0.0,
            "no_travel_miles": 0.0,
            "unavailable_miles": 0.0,
            "average_risk": 0.0,
            "has_no_travel": False,
            "has_unavailable": False,
            "total_distance_miles": round(total_distance_miles, 1),
            "travel_duration_hours": round(travel_duration_hours, 2),
            "evaluated_segments_count": 0,
        }

    # If only 1 checkpoint exists (e.g. 0-mile trip)
    if len(checkpoints) == 1:
        cp_risk = checkpoints[0].get("weather", {}).get("risk_level", RiskLevel.LOW.value)
        is_no_travel = (cp_risk == RiskLevel.NO_TRAVEL.value)
        is_unavail = (cp_risk == RiskLevel.UNAVAILABLE.value)
        score = RISK_NUMERICAL_SCALE.get(cp_risk, 0.0)
        return {
            "severe_risk_miles": total_distance_miles if cp_risk == RiskLevel.SEVERE.value else 0.0,
            "high_risk_miles": total_distance_miles if cp_risk == RiskLevel.HIGH.value else 0.0,
            "moderate_risk_miles": total_distance_miles if cp_risk == RiskLevel.MODERATE.value else 0.0,
            "low_risk_miles": total_distance_miles if cp_risk == RiskLevel.LOW.value else 0.0,
            "no_travel_miles": total_distance_miles if is_no_travel else 0.0,
            "unavailable_miles": total_distance_miles if is_unavail else 0.0,
            "average_risk": score,
            "has_no_travel": is_no_travel,
            "has_unavailable": is_unavail,
            "total_distance_miles": round(total_distance_miles, 1),
            "travel_duration_hours": round(travel_duration_hours, 2),
            "evaluated_segments_count": 0,
        }

    severe_miles = 0.0
    high_miles = 0.0
    moderate_miles = 0.0
    low_miles = 0.0
    no_travel_miles = 0.0
    unavailable_miles = 0.0

    weighted_risk_sum = 0.0
    evaluated_distance = 0.0

    has_no_travel_cp = False
    has_unavailable_cp = False

    # Checkpoint-level check for exposure
    for cp in checkpoints:
        r_level = cp.get("weather", {}).get("risk_level", RiskLevel.LOW.value)
        if r_level == RiskLevel.NO_TRAVEL.value:
            has_no_travel_cp = True
        elif r_level == RiskLevel.UNAVAILABLE.value:
            has_unavailable_cp = True

    # Segment-level distance-weighted exposure
    for i in range(len(checkpoints) - 1):
        cp_start = checkpoints[i]
        cp_end = checkpoints[i + 1]

        dist_start = cp_start.get("distance_miles", 0.0)
        dist_end = cp_end.get("distance_miles", 0.0)
        seg_dist = max(0.0, dist_end - dist_start)

        risk_start = cp_start.get("weather", {}).get("risk_level", RiskLevel.LOW.value)
        risk_end = cp_end.get("weather", {}).get("risk_level", RiskLevel.LOW.value)

        # Segment takes the worse of the two endpoint risks (conservative approach)
        seg_risk = _worse_risk(risk_start, risk_end)

        if seg_risk == RiskLevel.NO_TRAVEL.value:
            no_travel_miles += seg_dist
            has_no_travel_cp = True
            weighted_risk_sum += RISK_NUMERICAL_SCALE[RiskLevel.NO_TRAVEL.value] * seg_dist
            evaluated_distance += seg_dist
        elif seg_risk == RiskLevel.SEVERE.value:
            severe_miles += seg_dist
            weighted_risk_sum += RISK_NUMERICAL_SCALE[RiskLevel.SEVERE.value] * seg_dist
            evaluated_distance += seg_dist
        elif seg_risk == RiskLevel.HIGH.value:
            high_miles += seg_dist
            weighted_risk_sum += RISK_NUMERICAL_SCALE[RiskLevel.HIGH.value] * seg_dist
            evaluated_distance += seg_dist
        elif seg_risk == RiskLevel.MODERATE.value:
            moderate_miles += seg_dist
            weighted_risk_sum += RISK_NUMERICAL_SCALE[RiskLevel.MODERATE.value] * seg_dist
            evaluated_distance += seg_dist
        elif seg_risk == RiskLevel.UNAVAILABLE.value:
            unavailable_miles += seg_dist
            has_unavailable_cp = True
            # For unavailable segments, do not include in average risk denominator to avoid masking
        else:
            low_miles += seg_dist
            weighted_risk_sum += RISK_NUMERICAL_SCALE[RiskLevel.LOW.value] * seg_dist
            evaluated_distance += seg_dist

    average_risk = (
        round(weighted_risk_sum / evaluated_distance, 2)
        if evaluated_distance > 0.0
        else 0.0
    )

    return {
        "severe_risk_miles": round(severe_miles, 1),
        "high_risk_miles": round(high_miles, 1),
        "moderate_risk_miles": round(moderate_miles, 1),
        "low_risk_miles": round(low_miles, 1),
        "no_travel_miles": round(no_travel_miles, 1),
        "unavailable_miles": round(unavailable_miles, 1),
        "average_risk": average_risk,
        "has_no_travel": bool(has_no_travel_cp or no_travel_miles > 0),
        "has_unavailable": bool(has_unavailable_cp or unavailable_miles > 0),
        "total_distance_miles": round(total_distance_miles, 1),
        "travel_duration_hours": round(travel_duration_hours, 2),
        "evaluated_segments_count": len(checkpoints) - 1,
    }


def _format_duration(seconds: float) -> str:
    """Format duration in hours and minutes."""
    total_minutes = round(seconds / 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h {m:02d}m"


def _generate_recommendation_explanation(
    winner: dict[str, Any],
    all_eligible: list[dict[str, Any]],
    all_routes: list[dict[str, Any]]
) -> str:
    """
    Generate a concise, deterministic explanation for why the winning route was selected,
    reflecting actual calculations according to the four priority criteria:
    1. Fewest Severe miles
    2. Fewest High miles
    3. Lowest average risk
    4. Shortest travel time
    """
    winner_summary = winner.get("risk_summary", {})
    w_severe = winner_summary.get("severe_risk_miles", 0.0)
    w_high = winner_summary.get("high_risk_miles", 0.0)
    w_avg = winner_summary.get("average_risk", 0.0)
    w_duration = winner.get("duration_seconds", 0.0)

    # Case 1: Winner is the only eligible corridor among multiple routes
    if len(all_eligible) == 1 and len(all_routes) > 1:
        ineligible_reasons = []
        for r in all_routes:
            if r.get("route_id") != winner.get("route_id"):
                reason = r.get("ineligibility_reason")
                if reason and reason not in ineligible_reasons:
                    ineligible_reasons.append(reason)
        reason_str = "; ".join(ineligible_reasons) if ineligible_reasons else "other corridors have safety hazards"
        return f"Only eligible corridor: {reason_str}."

    # Case 2: Only 1 route was generated altogether
    if len(all_routes) == 1:
        return f"Safest available route ({w_severe:.1f} severe mi, {w_high:.1f} high mi, average risk {w_avg:.2f})."

    # Case 3: Multiple eligible corridors. Compare winner with the runner-up (index 1)
    runner_up = all_eligible[1]
    ru_summary = runner_up.get("risk_summary", {})
    ru_severe = ru_summary.get("severe_risk_miles", 0.0)
    ru_high = ru_summary.get("high_risk_miles", 0.0)
    ru_avg = ru_summary.get("average_risk", 0.0)
    ru_duration = runner_up.get("duration_seconds", 0.0)

    # Priority 1: Fewest Severe miles
    if w_severe < ru_severe:
        return (
            f"Selected for fewest severe-risk miles ({w_severe:.1f} mi vs {ru_severe:.1f} mi on alternative)."
        )

    # Priority 2: Fewest High miles (when severe miles are equal)
    if w_high < ru_high:
        return (
            f"Selected for lower high-risk exposure ({w_high:.1f} mi vs {ru_high:.1f} mi) with equal severe-risk miles."
        )

    # Priority 3: Lowest average risk (when severe and high miles are equal)
    if w_avg < ru_avg:
        return (
            f"Selected for lowest average weather risk score ({w_avg:.2f} vs {ru_avg:.2f}) across the corridor."
        )

    # Priority 4: Shortest travel time (when safety metrics are equal)
    if w_duration < ru_duration:
        time_diff_min = round((ru_duration - w_duration) / 60)
        return (
            f"Selected for shortest travel time ({_format_duration(w_duration)} vs {_format_duration(ru_duration)}, {time_diff_min}m faster) among equally safe alternatives."
        )

    # Fallback if identical
    return "Selected as optimal route satisfying all safety and travel time criteria."


def rank_and_recommend_routes(routes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Ranks routes using strict lexicographic order of assignment priorities:
    1. Fewest Severe miles
    2. Fewest High miles
    3. Lowest average risk
    4. Shortest travel time

    Handles No Travel and Unavailable conditions:
    - Any route with No Travel is marked ineligible.
    - Any route with Unavailable weather data is marked ineligible.
    - If no route is eligible, returns has_recommendation=False with clear communication.
    """
    if not routes:
        return {
            "recommended_route_id": None,
            "has_recommendation": False,
            "reason": "No routes available to evaluate.",
            "evaluated_routes_count": 0,
            "eligible_routes_count": 0,
            "ranked_routes": [],
        }

    eligible_routes: list[dict[str, Any]] = []
    ineligible_routes: list[dict[str, Any]] = []

    for route in routes:
        summary = route.get("risk_summary", {})
        has_no_travel = summary.get("has_no_travel", False)
        has_unavailable = summary.get("has_unavailable", False)

        if has_no_travel:
            route["is_eligible"] = False
            route["ineligibility_reason"] = "Unsuitable for travel: corridor crosses No Travel weather hazard."
            ineligible_routes.append(route)
        elif has_unavailable:
            route["is_eligible"] = False
            route["ineligibility_reason"] = "Ineligible: weather forecast data unavailable along corridor."
            ineligible_routes.append(route)
        else:
            route["is_eligible"] = True
            route["ineligibility_reason"] = None
            eligible_routes.append(route)

    # Lexicographic sorting of eligible routes:
    # 1. severe_risk_miles
    # 2. high_risk_miles
    # 3. average_risk
    # 4. duration_seconds
    def sort_key(r: dict[str, Any]) -> tuple[float, float, float, float]:
        s = r.get("risk_summary", {})
        return (
            round(s.get("severe_risk_miles", 0.0), 2),
            round(s.get("high_risk_miles", 0.0), 2),
            round(s.get("average_risk", 0.0), 2),
            round(r.get("duration_seconds", 0.0), 1),
        )

    eligible_routes.sort(key=sort_key)

    ranked_routes = []
    current_rank = 1

    for r in eligible_routes:
        r["rank"] = current_rank
        current_rank += 1
        ranked_routes.append(r)

    for r in ineligible_routes:
        r["rank"] = None
        r["is_recommended"] = False
        r["recommendation_reason"] = None
        ranked_routes.append(r)

    # Check recommendation outcome
    if not eligible_routes:
        # Determine why no recommendation is possible
        all_no_travel = all(r.get("risk_summary", {}).get("has_no_travel") for r in routes)
        all_unavailable = all(r.get("risk_summary", {}).get("has_unavailable") for r in routes)

        if all_no_travel:
            fail_reason = "No safe corridor recommendation available: all alternative routes contain segments classified as No Travel."
        elif all_unavailable:
            fail_reason = "No safe corridor recommendation available: weather data is unavailable or outside forecast horizon."
        else:
            fail_reason = "No safe corridor recommendation available: all alternatives either contain No Travel segments or missing forecast data."

        for r in routes:
            r["is_recommended"] = False
            r["recommendation_reason"] = None

        return {
            "recommended_route_id": None,
            "has_recommendation": False,
            "reason": fail_reason,
            "evaluated_routes_count": len(routes),
            "eligible_routes_count": 0,
            "ranked_routes": ranked_routes,
        }

    # Winning route is the first eligible route
    winner = eligible_routes[0]
    winning_id = winner["route_id"]
    explanation = _generate_recommendation_explanation(winner, eligible_routes, routes)

    for r in routes:
        if r["route_id"] == winning_id:
            r["is_recommended"] = True
            r["recommendation_reason"] = explanation
        else:
            r["is_recommended"] = False
            r["recommendation_reason"] = None

    return {
        "recommended_route_id": winning_id,
        "has_recommendation": True,
        "reason": explanation,
        "evaluated_routes_count": len(routes),
        "eligible_routes_count": len(eligible_routes),
        "ranked_routes": ranked_routes,
    }
