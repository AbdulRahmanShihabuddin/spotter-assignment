"""
Serializers for Route Generation API requests and responses with weather integration.
"""
from rest_framework import serializers
from django.utils import timezone


class RoutePlanRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(
        max_length=255,
        required=True,
        error_messages={
            "required": "Origin location is required.",
            "blank": "Origin location cannot be empty.",
        }
    )
    destination = serializers.CharField(
        max_length=255,
        required=True,
        error_messages={
            "required": "Destination location is required.",
            "blank": "Destination location cannot be empty.",
        }
    )
    departure_time = serializers.DateTimeField(
        required=False,
        default=timezone.now,
        error_messages={
            "invalid": "Departure time must be a valid ISO 8601 date and time."
        }
    )
    weight_lbs = serializers.FloatField(
        required=False,
        default=35000.0,
        min_value=1.0,
        max_value=120000.0,
        error_messages={
            "min_value": "Truck weight must be greater than 0 lbs.",
            "max_value": "Truck weight cannot exceed 120,000 lbs (over legal oversize/overweight permit limits).",
        }
    )
    checkpoint_interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25,
        error_messages={
            "invalid_choice": "Checkpoint sampling interval must be 10, 25, or 50 miles."
        }
    )

    def validate(self, attrs):
        origin = attrs.get("origin", "").strip()
        destination = attrs.get("destination", "").strip()

        if not origin:
            raise serializers.ValidationError({"origin": "Origin location cannot be blank."})
        if not destination:
            raise serializers.ValidationError({"destination": "Destination location cannot be blank."})

        if origin.lower() == destination.lower():
            raise serializers.ValidationError({
                "destination": "Destination cannot be identical to the origin location."
            })

        attrs["origin"] = origin
        attrs["destination"] = destination
        return attrs


class CheckpointWeatherSerializer(serializers.Serializer):
    is_available = serializers.BooleanField()
    wind_mph = serializers.FloatField(allow_null=True)
    rain_in_hr = serializers.FloatField(allow_null=True)
    snow_in_hr = serializers.FloatField(allow_null=True)
    forecast_time = serializers.CharField(allow_null=True, required=False)
    wind_risk = serializers.CharField()
    rain_risk = serializers.CharField()
    snow_risk = serializers.CharField()
    risk_level = serializers.CharField()


class HourlyForecastItemSerializer(serializers.Serializer):
    time = serializers.CharField()
    wind_mph = serializers.FloatField(allow_null=True)
    rain_in_hr = serializers.FloatField(allow_null=True)
    snow_in_hr = serializers.FloatField(allow_null=True)


class CheckpointSerializer(serializers.Serializer):
    id = serializers.CharField()
    sequence = serializers.IntegerField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance_miles = serializers.FloatField()
    distance_meters = serializers.FloatField()
    estimated_elapsed_seconds = serializers.FloatField()
    estimated_arrival_time = serializers.CharField()
    weather = CheckpointWeatherSerializer(required=False)
    hourly_forecast = HourlyForecastItemSerializer(many=True, required=False)


class GeoJSONGeometrySerializer(serializers.Serializer):
    type = serializers.CharField()
    coordinates = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField(),
            min_length=2,
            max_length=3
        )
    )


class RiskCountsSerializer(serializers.Serializer):
    low = serializers.IntegerField(default=0)
    moderate = serializers.IntegerField(default=0)
    high = serializers.IntegerField(default=0)
    severe = serializers.IntegerField(default=0)
    no_travel = serializers.IntegerField(default=0)
    unavailable = serializers.IntegerField(default=0)


class RiskSummarySerializer(serializers.Serializer):
    severe_risk_miles = serializers.FloatField(default=0.0)
    high_risk_miles = serializers.FloatField(default=0.0)
    moderate_risk_miles = serializers.FloatField(default=0.0)
    low_risk_miles = serializers.FloatField(default=0.0)
    no_travel_miles = serializers.FloatField(default=0.0)
    unavailable_miles = serializers.FloatField(default=0.0)
    average_risk = serializers.FloatField(default=0.0)
    has_no_travel = serializers.BooleanField(default=False)
    has_unavailable = serializers.BooleanField(default=False)
    total_distance_miles = serializers.FloatField(default=0.0)
    travel_duration_hours = serializers.FloatField(default=0.0)
    evaluated_segments_count = serializers.IntegerField(default=0)


class RouteOptionSerializer(serializers.Serializer):
    route_id = serializers.CharField()
    name = serializers.CharField()
    distance_meters = serializers.FloatField()
    distance_miles = serializers.FloatField()
    duration_seconds = serializers.FloatField()
    duration_hours = serializers.FloatField()
    geometry = GeoJSONGeometrySerializer()
    checkpoints = CheckpointSerializer(many=True)
    checkpoint_count = serializers.IntegerField()
    is_mock = serializers.BooleanField()
    provider = serializers.CharField()
    max_risk_level = serializers.CharField(default="Low")
    risk_counts = RiskCountsSerializer(required=False)
    risk_summary = RiskSummarySerializer(required=False)
    is_recommended = serializers.BooleanField(default=False)
    recommendation_reason = serializers.CharField(allow_null=True, required=False)
    is_eligible = serializers.BooleanField(default=True)
    ineligibility_reason = serializers.CharField(allow_null=True, required=False)
    rank = serializers.IntegerField(allow_null=True, required=False)


class RecommendationSerializer(serializers.Serializer):
    recommended_route_id = serializers.CharField(allow_null=True)
    has_recommendation = serializers.BooleanField()
    reason = serializers.CharField()
    evaluated_routes_count = serializers.IntegerField()
    eligible_routes_count = serializers.IntegerField()


class GeocodedLocationSerializer(serializers.Serializer):
    name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    display_name = serializers.CharField()


class RoutePlanResponseSerializer(serializers.Serializer):
    origin = GeocodedLocationSerializer()
    destination = GeocodedLocationSerializer()
    departure_time = serializers.DateTimeField()
    weight_lbs = serializers.FloatField()
    checkpoint_interval_miles = serializers.IntegerField()
    routes = RouteOptionSerializer(many=True)
    total_routes_found = serializers.IntegerField()
    recommendation = RecommendationSerializer(required=False)
