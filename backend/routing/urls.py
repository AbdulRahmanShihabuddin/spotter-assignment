from django.urls import path
from routing.views import RoutePlanView, HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('routes/plan/', RoutePlanView.as_view(), name='route-plan'),
]
