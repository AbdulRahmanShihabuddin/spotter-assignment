"""
API views for Weather-Aware Truck Routing with weather integration.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from routing.serializers import RoutePlanRequestSerializer, RoutePlanResponseSerializer
from routing.services import (
    get_geocoding_service,
    get_routing_provider,
    get_weather_provider,
    RiskLevel,
    calculate_route_risk_summary,
    rank_and_recommend_routes,
)
from routing.services.risk_engine import RISK_SEVERITY_ORDER
from routing.exceptions import RoutingAppError, GeocodingNotFoundError, NoRoutesFoundError

logger = logging.getLogger(__name__)


class RoutePlanView(APIView):
    """
    POST /api/routes/plan/
    Accepts trip parameters (origin, destination, departure_time, weight_lbs, checkpoint_interval_miles)
    and returns geocoded coordinates, route alternatives with geometries, distances, durations,
    and weather-risk classified checkpoints.
    """

    def post(self, request, *args, **kwargs):
        serializer = RoutePlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": "Validation failed",
                    "details": serializer.errors,
                    "code": "invalid_parameters",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        origin_query = data["origin"]
        dest_query = data["destination"]
        departure_time = data["departure_time"]
        weight_lbs = data["weight_lbs"]
        interval_miles = data["checkpoint_interval_miles"]

        geocoding_service = get_geocoding_service()
        routing_provider = get_routing_provider()
        weather_provider = get_weather_provider()

        # Step 1: Geocode Origin and Destination
        try:
            origin_loc = geocoding_service.geocode(origin_query)
        except GeocodingNotFoundError as e:
            return Response(
                {"error": "Origin not found", "detail": e.message, "code": e.code},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoutingAppError as e:
            return Response(
                {"error": "Geocoding error", "detail": e.message, "code": e.code},
                status=getattr(e, "status_code", status.HTTP_502_BAD_GATEWAY)
            )
        except Exception as e:
            logger.exception("Unexpected error geocoding origin '%s': %s", origin_query, str(e))
            return Response(
                {"error": "Internal geocoding error", "detail": "An unexpected error occurred during geocoding."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            dest_loc = geocoding_service.geocode(dest_query)
        except GeocodingNotFoundError as e:
            return Response(
                {"error": "Destination not found", "detail": e.message, "code": e.code},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoutingAppError as e:
            return Response(
                {"error": "Geocoding error", "detail": e.message, "code": e.code},
                status=getattr(e, "status_code", status.HTTP_502_BAD_GATEWAY)
            )
        except Exception as e:
            logger.exception("Unexpected error geocoding destination '%s': %s", dest_query, str(e))
            return Response(
                {"error": "Internal geocoding error", "detail": "An unexpected error occurred during geocoding."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Request Alternative Routes from Routing Provider
        try:
            routes = routing_provider.get_routes(
                origin=origin_loc,
                destination=dest_loc,
                departure_time=departure_time,
                checkpoint_interval_miles=interval_miles,
                weight_lbs=weight_lbs
            )
        except NoRoutesFoundError as e:
            return Response(
                {"error": "No routes found", "detail": e.message, "code": e.code},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoutingAppError as e:
            return Response(
                {"error": "Routing failure", "detail": e.message, "code": e.code},
                status=getattr(e, "status_code", status.HTTP_502_BAD_GATEWAY)
            )
        except Exception as e:
            logger.exception("Unexpected routing calculation failure: %s", str(e))
            return Response(
                {"error": "Routing calculation error", "detail": "An unexpected error occurred while generating routes."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 3: Enrich Checkpoints with Weather Forecasts and Risk Classification
        for route in routes:
            raw_checkpoints = route.get("checkpoints", [])
            enriched_checkpoints = weather_provider.enrich_checkpoints(
                checkpoints=raw_checkpoints,
                weight_lbs=weight_lbs,
                departure_time=departure_time
            )
            route["checkpoints"] = enriched_checkpoints

            # Compute route risk summary
            counts = {
                "low": 0,
                "moderate": 0,
                "high": 0,
                "severe": 0,
                "no_travel": 0,
                "unavailable": 0,
            }
            highest_severity_rank = -1
            max_risk = RiskLevel.LOW.value

            for cp in enriched_checkpoints:
                w_info = cp.get("weather", {})
                r_level = w_info.get("risk_level", RiskLevel.LOW.value)
                slug = r_level.lower().replace(" ", "_")
                if slug in counts:
                    counts[slug] += 1

                rank = RISK_SEVERITY_ORDER.get(r_level, 0)
                if rank > highest_severity_rank:
                    highest_severity_rank = rank
                    max_risk = r_level

            if highest_severity_rank <= 0 and counts["unavailable"] > 0:
                max_risk = RiskLevel.UNAVAILABLE.value

            route["max_risk_level"] = max_risk
            route["risk_counts"] = counts

            # Step 4: Calculate Distance-Weighted Route Risk Summary
            risk_summary = calculate_route_risk_summary(
                checkpoints=enriched_checkpoints,
                total_distance_miles=route.get("distance_miles", 0.0),
                travel_duration_hours=route.get("duration_hours", 0.0),
            )
            route["risk_summary"] = risk_summary

        # Step 5: Rank and Recommend Safest Corridor
        recommendation = rank_and_recommend_routes(routes)

        response_payload = {
            "origin": origin_loc.to_dict(),
            "destination": dest_loc.to_dict(),
            "departure_time": departure_time.isoformat(),
            "weight_lbs": weight_lbs,
            "checkpoint_interval_miles": interval_miles,
            "routes": routes,
            "total_routes_found": len(routes),
            "recommendation": recommendation,
        }

        # Validate with response serializer before returning
        out_serializer = RoutePlanResponseSerializer(data=response_payload)
        if not out_serializer.is_valid():
            logger.error("Response serialization errors: %s", out_serializer.errors)
            return Response(
                {"error": "Serialization error", "details": out_serializer.errors},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(out_serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    GET /api/health/
    Verifies API availability and configuration status.
    """
    def get(self, request, *args, **kwargs):
        provider = getattr(settings, "ROUTING_PROVIDER", "osrm")
        use_mock = getattr(settings, "USE_MOCK_ROUTING", False)
        weather_provider = getattr(settings, "WEATHER_PROVIDER", "open-meteo")
        use_mock_weather = getattr(settings, "USE_MOCK_WEATHER", False)

        return Response({
            "status": "healthy",
            "service": "weather-aware-truck-routing",
            "phase": "Phase 3: Route Recommendation, Weather Heatmap and Finalization",
            "routing_provider": "mock" if (use_mock and settings.DEBUG) else provider,
            "weather_provider": "mock" if use_mock_weather else weather_provider,
            "is_mock": bool(use_mock and settings.DEBUG),
            "debug": settings.DEBUG,
        }, status=status.HTTP_200_OK)
