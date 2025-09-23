from django.db.models import F, Count
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import datetime, timedelta

from airport.models import Flight, Airplane, AirplaneType, Route, Airport, Crew
from airport.serializers import FlightListSerializer, FlightDetailSerializer

FLIGHT_URL = reverse("airport:flight-list")
DETAIL_URL = lambda pk: reverse("airport:flight-detail", args=[pk])

def sample_airport(name="Source", city="City"):
    return Airport.objects.create(name=name, closest_big_city=city)

def sample_route(**params):
    defaults = {
        "source": sample_airport("Source"),
        "destination": sample_airport("Destination"),
        "distance": 1000,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)

def sample_airplane(**params):
    airplane_type = AirplaneType.objects.create(name="Boeing 747")
    defaults = {
        "name": "TestPlane",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)

def sample_crew(first_name="John", last_name="Doe"):
    return Crew.objects.create(first_name=first_name, last_name=last_name)

def sample_flight(**params):
    defaults = {
        "airplane": sample_airplane(),
        "route": sample_route(),
        "departure_time": datetime.now(),
        "arrival_time": datetime.now() + timedelta(hours=2),
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    if "crews" in params:
        for crew in params["crews"]:
            flight.crews.add(crew)
    return flight


class UnauthorizedFlightTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedFlightTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email="user@test.com", password="testpass")
        self.client.force_authenticate(self.user)

        self.flight = sample_flight()
        self.flight2 = sample_flight(
            departure_time=datetime.now() + timedelta(days=1)
        )
        self.crew1 = sample_crew(first_name="Alice", last_name="Smith")
        self.crew2 = sample_crew(first_name="Bob", last_name="Brown")
        self.flight.crews.add(self.crew1)
        self.flight2.crews.add(self.crew2)

    def test_list_flights(self):
        flights = Flight.objects.all().select_related(
            'airplane', 'airplane__airplane_type', 'route', 'route__source', 'route__destination'
        ).prefetch_related('crews').annotate(
            tickets_available=(
                    F('airplane__rows') * F('airplane__seats_in_row') - Count("tickets")
            ),
        )
        res = self.client.get(FLIGHT_URL)
        serializer = FlightListSerializer(flights, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_retrieve_flight(self):
        url = DETAIL_URL(self.flight.id)
        res = self.client.get(url)
        serializer = FlightDetailSerializer(self.flight)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_date(self):
        date_str = self.flight.departure_time.strftime("%Y-%m-%d")
        res = self.client.get(f"{FLIGHT_URL}?date={date_str}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.flight.id, [f["id"] for f in res.data["results"]])
        self.assertNotIn(self.flight2.id, [f["id"] for f in res.data["results"]])

    def test_filter_flights_by_crews(self):
        res = self.client.get(f"{FLIGHT_URL}?crews={self.crew1.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.flight.id, [f["id"] for f in res.data["results"]])
        self.assertNotIn(self.flight2.id, [f["id"] for f in res.data["results"]])

