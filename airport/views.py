from rest_framework import viewsets

from airport.models import (
    Airport,
    AirplaneType,
    Crew,
    Route,
    Airplane,
    Flight,
    Order,
    Ticket
)

from airport.serializers import (
    AirportSerializer,
    AirplaneTypeSerializer,
    CrewSerializer,
    RouteSerializer,
    AirplaneSerializer,
    FlightSerializer,
    OrderSerializer,
    TicketSerializer, RouteListSerializer, FlightListSerializer, FlightRetrieveSerializer, RouteRetrieveSerializer,
    CrewListSerializer, AirplaneListSerializer, TicketListSerializer, TicketRetrieveSerializer
)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        return CrewSerializer



class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related()

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteRetrieveSerializer

        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            return queryset.select_related("source", "destination")
        return queryset


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related()

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer

        return AirplaneSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            return queryset.select_related(
                "route__source",
                "route__destination",
                "airplane",
            ).prefetch_related("crew")

        if self.action == "retrieve":
            return queryset.select_related(
                "route__source",
                "route__destination",
                "airplane__airplane_type",
            ).prefetch_related("crew")

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            return queryset.select_related(
                "flight__route__source",
                "flight__route__destination",
            )
        if self.action == "retrieve":
            return queryset.select_related(
                "flight__route__source",
                "flight__route__destination",
                "flight__airplane__airplane_type",
            ).prefetch_related("flight__crew")

        return queryset
