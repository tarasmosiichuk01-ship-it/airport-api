from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Flight,
    Order,
    Ticket
)
from airport.serializers import (
    AirplaneListSerializer,
    AirplaneRetrieveSerializer,
    TicketSerializer
)

AIRPLANE_URL = reverse("airport:airplane-list")


def sample_airplane(**params) -> Airplane:
    airplane_type, _ = AirplaneType.objects.get_or_create(
        name="Test Airplane Type"
    )

    defaults = {
        "name": f"Test Airplane {Airplane.objects.count() + 1}",
        "rows": 1,
        "seats_in_row": 1,
        "airplane_type": airplane_type,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_flight():
    airplane_type = AirplaneType.objects.create(name="Test Type")
    airplane = Airplane.objects.create(
        name="Test Airplane",
        rows=5,
        seats_in_row=6,
        airplane_type=airplane_type
    )
    source = Airport.objects.create(name="Source", closest_big_city="City A")
    destination = Airport.objects.create(
        name="Dest",
        closest_big_city="City B"
    )
    route = Route.objects.create(
        source=source, destination=destination, distance=100
    )
    return Flight.objects.create(
        route=route,
        airplane=airplane,
        departure_time=timezone.now() + timedelta(days=1),
        arrival_time=timezone.now() + timedelta(days=1, hours=4),
    )


def detail_url(airplane_id: int):
    return reverse("airport:airplane-detail", args=[airplane_id])


class UnauthenticatedAirportTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPLANE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="test1234"
        )
        self.client.force_authenticate(self.user)

    def test_airplanes_list(self):
        sample_airplane()

        response = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all().order_by("id")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_airplanes_by_types(self):
        airplane_type_1 = AirplaneType.objects.create(name="Turboprop")
        airplane_type_2 = AirplaneType.objects.create(name="Wide-body")

        airplane_with_type_1 = sample_airplane(airplane_type=airplane_type_1)
        airplane_with_type_2 = sample_airplane(airplane_type=airplane_type_2)
        airplane_without_type = sample_airplane()

        response = self.client.get(
            AIRPLANE_URL,
            {"airplane_types": f"{airplane_type_1.id},{airplane_type_2.id}"}
        )

        serializer_with_type_1 = AirplaneListSerializer(airplane_with_type_1)
        serializer_with_type_2 = AirplaneListSerializer(airplane_with_type_2)
        serializer_without_type = AirplaneListSerializer(airplane_without_type)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_type_1.data, response.data["results"])
        self.assertIn(serializer_with_type_2.data, response.data["results"])
        self.assertNotIn(
            serializer_without_type.data,
            response.data["results"]
        )

    def test_filter_airplanes_by_name(self):
        airplane_1 = sample_airplane(name="Airbus A350")
        airplane_2 = sample_airplane(name="Boeing 747")

        response = self.client.get(AIRPLANE_URL, {"name": "Airbus"})

        serializer_1 = AirplaneListSerializer(airplane_1)
        serializer_2 = AirplaneListSerializer(airplane_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, response.data["results"])
        self.assertNotIn(serializer_2.data, response.data["results"])

    def test_retrieve_airplane_detail(self):
        airplane = sample_airplane()

        url = detail_url(airplane.id)
        response = self.client.get(url)
        serializer = AirplaneRetrieveSerializer(airplane)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_forbidden(self):
        payload = {
            "name": "Airbus A350",
            "rows": 1,
            "seats_in_row": 1,
        }

        response = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplanesTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="test1234",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = AirplaneType.objects.create(name="Test Type")
        payload = {
            "name": "Airbus A350",
            "rows": 1,
            "seats_in_row": 1,
            "airplane_type": airplane_type.id,
        }
        response = self.client.post(AIRPLANE_URL, payload)
        airplane = Airplane.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])
        self.assertEqual(airplane.airplane_type.id, payload["airplane_type"])

    def test_update_airplane(self):
        airplane = sample_airplane()
        airplane_type = AirplaneType.objects.create(name="New Type")
        payload = {
            "name": "Updated Airplane",
            "rows": 5,
            "seats_in_row": 10,
            "airplane_type": airplane_type.id,
        }
        url = reverse("airport:airplane-detail", args=[airplane.id])
        response = self.client.put(url, payload)

        airplane.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])
        self.assertEqual(airplane.airplane_type.id, payload["airplane_type"])

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane()
        url = detail_url(airplane.id)
        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TicketSerializerTests(TestCase):
    def setUp(self) -> None:
        self.flight = sample_flight()

    def test_ticket_invalid_seat(self):
        data = {"row": 1, "seat": 99, "flight": self.flight.id}
        serializer = TicketSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("seat", serializer.errors)

    def test_ticket_invalid_row(self):
        data = {"row": 99, "seat": 1, "flight": self.flight.id}
        serializer = TicketSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("row", serializer.errors)

    def test_ticket_duplicate_seat(self):
        user = get_user_model().objects.create_user(
            email="test@test.com", password="test1234"
        )
        order = Order.objects.create(user=user)
        Ticket.objects.create(flight=self.flight, order=order, row=1, seat=1)

        data = {"row": 1, "seat": 1, "flight": self.flight.id}
        serializer = TicketSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("seat", serializer.errors)
