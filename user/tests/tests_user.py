from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
ME_URL = reverse("user:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserSerializerTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payload = {
            "email": "test@test.com",
            "password": "test1234",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_create_user_password_too_short(self):
        payload = {"email": "test@test.com", "password": "123"}
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().objects.filter(email=payload["email"]).exists()
        )

    def test_create_user_email_already_exists(self):
        payload = {"email": "test@test.com", "password": "test1234"}
        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_success(self):
        create_user(email="test@test.com", password="test1234")
        payload = {"email": "test@test.com", "password": "test1234"}

        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_create_token_invalid_credentials(self):
        create_user(email="test@test.com", password="test1234")
        payload = {"email": "test@test.com", "password": "wrongpassword"}

        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("token", response.data)

    def test_create_token_missing_fields(self):
        response = self.client.post(TOKEN_URL, {"email": "test@test.com"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_retrieve_user_unauthorized(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_profile(self):
        user = create_user(email="test@test.com", password="test1234")
        self.client.force_authenticate(user)

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        self.assertNotIn("password", response.data)

    def test_update_user_password(self):
        user = create_user(email="test@test.com", password="test1234")
        self.client.force_authenticate(user)

        response = self.client.patch(ME_URL, {"password": "newpassword123"})

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password("newpassword123"))
