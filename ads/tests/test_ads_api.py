from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ads.models import Ad

User = get_user_model()


class AdApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = APIClient()
        url_token = reverse("token_obtain_pair")
        data = {"username": self.user.username, "password": "pass"}
        response = self.client.post(url_token, data, format="json")
        self.access = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access)
        self.ad1 = Ad.objects.create(
            user=self.user,
            title="Ad1",
            description="desc",
            category="cat",
            condition="new",
        )
        self.ad2 = Ad.objects.create(
            user=self.user,
            title="Ad2",
            description="desc",
            category="cat",
            condition="used",
        )

    def test_list_ads(self):
        url = reverse("ad-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_exchange_indicators(self):
        url = reverse("ad-exchange-indicators")
        data = {"ad_ids": [self.ad1.id, self.ad2.id]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("incoming", response.data)
        self.assertIn("outgoing", response.data)
        self.assertIn("exchange_map", response.data)

    def test_pagination(self):
        # Создаём 15 объявлений
        for i in range(15):
            Ad.objects.create(user=self.user, title=f'PagAd{i}', description='desc', category='cat', condition='new')
        url = reverse('ad-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 17)  # 2 из setUp + 15 новых
        # Вторая страница
        response2 = self.client.get(url + '?page=2', format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('results', response2.data)
        self.assertEqual(len(response2.data['results']), 7)
