from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

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


class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class AirplaneTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class CrewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class CrewListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Crew
        fields = ("id", "full_name")



class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(read_only=True, slug_field="name")
    destination = serializers.SlugRelatedField(read_only=True, slug_field="name")


class RouteRetrieveSerializer(RouteSerializer):
    source = AirportSerializer()
    destination = AirportSerializer()


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "capacity")


class AirplaneImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirplaneListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = ("id", "name")


class FlightSerializer(serializers.ModelSerializer):
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "crew", "departure_time", "arrival_time")


class FlightListSerializer(FlightSerializer):
    route = serializers.SlugRelatedField(read_only=True, slug_field="full_route")
    airplane = serializers.CharField(source="airplane.name", read_only=True)
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "crew", "departure_time", "arrival_time", "tickets_available")






class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")
        validators = []

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )

        if Ticket.objects.filter(
                flight=attrs["flight"],
                row=attrs["row"],
                seat=attrs["seat"]
        ).exists():
            raise serializers.ValidationError(
                {"seat": f"Seat {attrs['seat']} in row {attrs['row']} is already taken."}
            )

        return data


class TakenSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer()
    airplane = AirplaneSerializer()
    crew = CrewSerializer(many=True)
    taken_seats = TakenSeatSerializer(
        many=True,
        read_only=True,
        source="tickets",
    )

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "crew", "departure_time", "arrival_time", "taken_seats")

class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)
    user = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets", "user")

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets:
                Ticket.objects.create(order=order, **ticket)
            return order


class TicketListSerializer(serializers.ModelSerializer):

    flight_route = serializers.CharField(source="flight.route.full_route")
    departure_time = serializers.DateTimeField(source="flight.departure_time", format="%Y-%m-%d %H:%M")
    arrival_time = serializers.DateTimeField(source="flight.arrival_time", format="%Y-%m-%d %H:%M")

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight_route", "departure_time", "arrival_time")




class TicketRetrieveSerializer(TicketSerializer):
    flight = FlightRetrieveSerializer()


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)