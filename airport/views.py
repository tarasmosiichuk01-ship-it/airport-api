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
        if self.action == "list":
            return queryset.select_related("source", "destination")
        return queryset


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()

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
            return queryset.prefetch_related("crew")

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer
