from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

from airport.models import Airport
from airport.serializers import AirportSerializer

URL = reverse("airport:airport-list")
DETAIL_URL = lambda pk: reverse("airport:airport-detail", args=[pk])

def sample_airport(**params):
    defaults = {
        "name": "Test Airport",
        "closest_big_city": "Test City"
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


class UnauthorizedAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="testpass"
        )
        self.client.force_authenticate(self.user)

        self.airport = sample_airport()
        self.airport2 = sample_airport(name="Another Airport", closest_big_city="Another City")

    def test_list_airports(self):
        res = self.client.get(URL)
        airports = Airport.objects.all()
        serializer = AirportSerializer(airports, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_airports_by_name(self):
        res = self.client.get(f"{URL}?name=Test")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "Test Airport")

        res = self.client.get(f"{URL}?name=NonExisting")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_filter_airports_by_city(self):
        res = self.client.get(f"{URL}?city=Another")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["closest_big_city"], "Another City")


class AdminAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com", password="adminpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_post_airport(self):
        payload = {
            "name": "Admin Airport",
            "closest_big_city": "Admin City"
        }
        res = self.client.post(URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        airport = Airport.objects.get(id=res.data["id"])
        self.assertEqual(airport.name, payload["name"])
        self.assertEqual(airport.closest_big_city, payload["closest_big_city"])
