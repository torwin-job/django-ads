from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.username = "jwtuser"
        self.password = "jwtpass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
        self.client = APIClient()

    def test_register(self):
        url = reverse("api_register")
        data = {"username": "newjwtuser", "password": "newpass"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newjwtuser").exists())

    def test_jwt_token_obtain(self):
        url = reverse("token_obtain_pair")
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access = response.data["access"]
        self.refresh = response.data["refresh"]

    def test_jwt_token_refresh(self):
        url = reverse("token_obtain_pair")
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        refresh = response.data["refresh"]
        url_refresh = reverse("token_refresh")
        response_refresh = self.client.post(
            url_refresh, {"refresh": refresh}, format="json"
        )
        self.assertEqual(response_refresh.status_code, status.HTTP_200_OK)
        self.assertIn("access", response_refresh.data)

    def test_logout(self):
        url = reverse("token_obtain_pair")
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        access = response.data["access"]
        refresh = response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access)
        url_logout = reverse("api_logout")
        response_logout = self.client.post(
            url_logout, {"refresh": refresh}, format="json"
        )
        self.assertEqual(response_logout.status_code, status.HTTP_205_RESET_CONTENT)
