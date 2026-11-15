"""
Custom exceptions for the routing app.
"""

class RoutingAppError(Exception):
    """Base exception for routing application."""
    def __init__(self, message: str, code: str = "routing_error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class GeocodingError(RoutingAppError):
    """Raised when geocoding fails."""
    def __init__(self, message: str, code: str = "geocoding_error", status_code: int = 400):
        super().__init__(message, code=code, status_code=status_code)


class GeocodingNotFoundError(GeocodingError):
    """Raised when a location could not be resolved."""
    def __init__(self, query: str):
        super().__init__(
            f"Unable to find location for: '{query}'. Please check the spelling or provide a more specific address.",
            code="location_not_found",
            status_code=404
        )


class RoutingProviderError(RoutingAppError):
    """Raised when the routing provider fails."""
    def __init__(self, message: str, provider: str = "unknown", code: str = "provider_error", status_code: int = 502):
        super().__init__(message, code=code, status_code=status_code)
        self.provider = provider


class NoRoutesFoundError(RoutingAppError):
    """Raised when no route could be found between origin and destination."""
    def __init__(self, origin: str, destination: str):
        super().__init__(
            f"No drivable route found between '{origin}' and '{destination}'.",
            code="no_routes_found",
            status_code=404
        )
