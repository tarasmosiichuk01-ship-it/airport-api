from datetime import datetime
from django.db.models import Count, F
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

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
    TicketSerializer,
    RouteListSerializer,
    FlightListSerializer,
    FlightRetrieveSerializer,
    RouteRetrieveSerializer,
    CrewListSerializer,
    AirplaneListSerializer,
    TicketListSerializer,
    TicketRetrieveSerializer,
    AirplaneImageSerializer,
    OrderListSerializer,
    AirplaneRetrieveSerializer
)


class BasePagination(PageNumberPagination):
    page_size = 3
    max_page_size = 100


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    pagination_class = BasePagination

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


class AirplaneViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Airplane.objects.select_related()
    pagination_class = BasePagination

    @staticmethod
    def _params_to_ints(query_string):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "retrieve":
            return AirplaneRetrieveSerializer
        elif self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset

        airplane_types = self.request.query_params.get("airplane_types")
        name = self.request.query_params.get("name")

        if airplane_types:
            airplane_types = self._params_to_ints(airplane_types)
            queryset = queryset.filter(airplane_type__id__in=airplane_types)

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific movie"""
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "airplane_types",
                type={"type": "array", "items": {"type": "number"}},
                description=(
                        "Filter by airplane type id ex. ?airplane_types=2,3"
                ),
                required=False,
                explode=False,
            ),
            OpenApiParameter(
                "name",
                type=str,
                description="Filter by airplane name",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of airplane."""
        return super().list(request, *args, **kwargs)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = (
                queryset.select_related(
                    "route__source",
                    "route__destination",
                    "airplane",
                )
                .prefetch_related("crew")
                .annotate(
                    tickets_available=(
                        F("airplane__rows")
                        * F("airplane__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "route__source",
                "route__destination",
                "airplane__airplane_type",
            ).prefetch_related("crew")

        return queryset.order_by("id")


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")

        queryset = self.queryset.filter(user=self.request.user)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__date=date)

        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date",
                type=datetime,
                description="Filter by date in format: 'year-month-day'",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of orders"""
        return super().list(request, *args, **kwargs)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    pagination_class = BasePagination

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
            ).prefetch_related("flight__crew", "flight__tickets")

        return queryset
