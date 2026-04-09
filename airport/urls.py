from django.urls import path, include
from rest_framework import routers

from airport.views import AirportViewSet, AirplaneTypeViewSet, CrewViewSet, RouteViewSet, FlightViewSet, OrderViewSet, \
    TicketViewSet, AirplaneViewSet

app_name = "airport"

router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("airplane-types", AirplaneTypeViewSet, basename="airplane-type")
router.register("crews", CrewViewSet)
router.register("routes", RouteViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)
router.register("tickets", TicketViewSet)

urlpatterns = [
    path("", include(router.urls)),
]