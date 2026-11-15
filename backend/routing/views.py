"""
API views for Weather-Aware Truck Routing.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from routing.serializers import RoutePlanRequestSerializer, RoutePlanResponseSerializer
from routing.services import get_geocoding_service, get_routing_provider
from routing.exceptions import RoutingAppError, GeocodingNotFoundError, NoRoutesFoundError

logger = logging.getLogger(__name__)


class RoutePlanView(APIView):
    """
    POST /api/routes/plan/
    Accepts trip parameters (origin, destination, departure_time, weight_lbs, checkpoint_interval_miles)
    and returns geocoded coordinates, route alternatives with geometries, distances, durations, and checkpoints.
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

        response_payload = {
            "origin": origin_loc.to_dict(),
            "destination": dest_loc.to_dict(),
            "departure_time": departure_time.isoformat(),
            "weight_lbs": weight_lbs,
            "checkpoint_interval_miles": interval_miles,
            "routes": routes,
            "total_routes_found": len(routes),
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
        return Response({
            "status": "healthy",
            "service": "weather-aware-truck-routing",
            "phase": "Phase 1: Project Foundation and Route Generation",
            "routing_provider": "mock" if (use_mock and settings.DEBUG) else provider,
            "is_mock": bool(use_mock and settings.DEBUG),
            "debug": settings.DEBUG,
        }, status=status.HTTP_200_OK)
