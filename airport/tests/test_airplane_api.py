import os
import tempfile

from PIL import Image
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase

from airport.models import Airplane, AirplaneType
from airport.serializers import AirplaneListSerializer, AirplaneDetailSerializer

URL = reverse("airport:airplane-list")
DETAIL_URL = lambda pk: reverse("airport:airplane-detail", args=[pk])

def sample_airplane_type(name="Boeing 747"):
    return AirplaneType.objects.create(name=name)

def sample_airplane(**params):
    defaults = {
        "name": "TestPlane",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": sample_airplane_type(),
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def image_upload_url(airplane_id):
    """Return URL for airplane image upload"""
    return reverse("airport:airplane-upload-image", args=[airplane_id])


def detail_url(airplane_id):
    """Return URL for airplane detail"""
    return reverse("airport:airplane-detail", args=[airplane_id])


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="password"
        )
        self.client.force_authenticate(self.user)
        self.airplane_type = sample_airplane_type()
        self.airplane = sample_airplane(airplane_type=self.airplane_type)

    def tearDown(self):
        if self.airplane.image:
            self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        """Test uploading an image to airplane"""
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.airplane.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_url_is_shown_on_airplane_detail(self):
        """Check that image URL is returned in detail view"""
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")

        res = self.client.get(detail_url(self.airplane.id))
        self.assertIn("image", res.data)

class UnauthorizedAirplaneTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedAirplaneTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="testpass"
        )
        self.client.force_authenticate(self.user)

        self.airplane = sample_airplane()
        self.airplane2 = sample_airplane(name="AnotherPlane")

    def test_list_airplanes(self):
        res = self.client.get(URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_airplane(self):
        url = DETAIL_URL(self.airplane.id)
        res = self.client.get(url)
        serializer = AirplaneDetailSerializer(self.airplane)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_airplanes_by_name(self):
        res = self.client.get(f"{URL}?name=TestPlane")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "TestPlane")

        res = self.client.get(f"{URL}?name=NonExisting")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_post_airplane_forbidden(self):
        payload = {
            "name": "ForbiddenPlane",
            "rows": 10,
            "seats_in_row": 6,
            "airplane_type": self.airplane.airplane_type.id,
        }
        res = self.client.post(URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com", password="adminpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.airplane_type = sample_airplane_type()

    def test_post_airplane(self):
        payload = {
            "name": "AdminPlane",
            "rows": 25,
            "seats_in_row": 8,
            "airplane_type": self.airplane_type.id,
        }
        res = self.client.post(URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        airplane = Airplane.objects.get(id=res.data["id"])
        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])
        self.assertEqual(airplane.airplane_type.id, payload["airplane_type"])