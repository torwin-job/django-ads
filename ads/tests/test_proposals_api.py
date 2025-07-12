from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ads.models import Ad, ExchangeProposal

User = get_user_model()


class ProposalApiTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.ad1 = Ad.objects.create(
            user=self.user1,
            title="Ad1",
            description="desc",
            category="cat",
            condition="new",
        )
        self.ad2 = Ad.objects.create(
            user=self.user2,
            title="Ad2",
            description="desc",
            category="cat",
            condition="used",
        )
        self.client = APIClient()
        url_token = reverse("token_obtain_pair")
        data = {"username": self.user1.username, "password": "pass"}
        response = self.client.post(url_token, data, format="json")
        self.access1 = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access1)
        self.proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1, ad_receiver=self.ad2, status="pending"
        )

    def test_list_proposals(self):
        url = reverse("exchangeproposal-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_set_status(self):
        url_token = reverse("token_obtain_pair")
        data = {"username": self.user2.username, "password": "pass"}
        response = self.client.post(url_token, data, format="json")
        access2 = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access2)
        url = reverse("exchangeproposal-set-status", args=[self.proposal.id])
        data = {"status": "accepted"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, "accepted")
