from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserApiTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.handler._force_reset_throttle = True

    def create_user(self, **params):
        defaults = {
            "email": "user@example.com",
            "password": "testpass123",
        }
        defaults.update(params)
        return User.objects.create_user(**defaults)

    def authenticate(self, user=None):
        if user is None:
            user = self.create_user()
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return user

    def test_create_user_success(self):
        payload = {"email": "new@example.com", "password": "strongpass"}
        res = self.client.post("/api/user/register/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data)
        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_create_user_password_too_short(self):
        payload = {"email": "short@example.com", "password": "123"}
        res = self.client.post("/api/user/register/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    def test_create_user_duplicate_email(self):
        self.create_user(email="dup@example.com")
        payload = {"email": "dup@example.com", "password": "anotherpass"}
        res = self.client.post("/api/user/register/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_profile_authenticated(self):
        user = self.authenticate()
        res = self.client.get("/api/user/me/")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)
        self.assertNotIn("password", res.data)

    def test_update_profile_authenticated(self):
        user = self.authenticate()
        payload = {"email": "updated@example.com", "password": "newpassword123"}
        res = self.client.patch("/api/user/me/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_retrieve_profile_unauthorized(self):
        res = self.client.get("/api/user/me/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
