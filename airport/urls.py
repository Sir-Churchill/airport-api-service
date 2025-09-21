from django.urls import path, include
from rest_framework import routers

from airport.views import AirportViewSet, RouteViewSet, AirplaneViewSet, AirplaneTypeViewSet, FlightViewSet, \
    OrderViewSet

app_name = 'airport'

router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)


urlpatterns = [
    path("", include(router.urls)),
]