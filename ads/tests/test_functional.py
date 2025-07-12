from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ads.models import Ad, ExchangeProposal
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class BarterPlatformTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass1")
        self.user2 = User.objects.create_user(username="user2", password="pass2")
        self.ad1 = Ad.objects.create(
            user=self.user1,
            title="Велосипед",
            description="Горный велосипед",
            category="Транспорт",
            condition="Б/У",
        )
        self.ad2 = Ad.objects.create(
            user=self.user2,
            title="Ноутбук",
            description="Игровой ноутбук",
            category="Электроника",
            condition="Новый",
        )

    def test_registration(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "testpassword123",
                "password2": "testpassword123",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_logout(self):
        login = self.client.login(username="user1", password="pass1")
        self.assertTrue(login)
        response = self.client.get(reverse("ad_list"))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse("ad_create"))
        self.assertRedirects(response, "/accounts/login/?next=/ad/create/")

    def test_create_ad(self):
        self.client.login(username="user1", password="pass1")
        response = self.client.post(
            reverse("ad_create"),
            {
                "title": "Книга",
                "description": "Детектив",
                "category": "Книги",
                "condition": "Новый",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.assertTrue(Ad.objects.filter(title="Книга").exists())

    def test_edit_ad(self):
        self.client.login(username="user1", password="pass1")
        response = self.client.post(
            reverse("ad_edit", args=[self.ad1.pk]),
            {
                "title": "Велосипед (обновлён)",
                "description": "Горный велосипед",
                "category": "Транспорт",
                "condition": "Б/У",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.ad1.refresh_from_db()
        self.assertEqual(self.ad1.title, "Велосипед (обновлён)")

    def test_edit_ad_no_permission(self):
        self.client.login(username="user2", password="pass2")
        response = self.client.post(
            reverse("ad_edit", args=[self.ad1.pk]),
            {
                "title": "Велосипед (чужой)",
                "description": "Горный велосипед",
                "category": "Транспорт",
                "condition": "Б/У",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.ad1.refresh_from_db()
        self.assertNotEqual(self.ad1.title, "Велосипед (чужой)")

    def test_delete_ad(self):
        self.client.login(username="user1", password="pass1")
        response = self.client.post(reverse("ad_delete", args=[self.ad1.pk]))
        self.assertRedirects(response, reverse("ad_list"))
        self.assertFalse(Ad.objects.filter(pk=self.ad1.pk).exists())

    def test_delete_ad_no_permission(self):
        self.client.login(username="user2", password="pass2")
        response = self.client.post(reverse("ad_delete", args=[self.ad1.pk]))
        self.assertRedirects(response, reverse("ad_list"))
        self.assertTrue(Ad.objects.filter(pk=self.ad1.pk).exists())

    def test_ad_list_search(self):
        response = self.client.get(reverse("ad_list"), {"q": "Велосипед"})
        self.assertContains(response, "Велосипед")
        self.assertNotContains(response, "Ноутбук")

    def test_ad_list_filter_category(self):
        response = self.client.get(reverse("ad_list"), {"category": "Электроника"})
        self.assertContains(response, "Ноутбук")
        self.assertNotContains(response, "Велосипед")

    def test_proposal_create(self):
        self.client.login(username="user1", password="pass1")
        response = self.client.post(
            reverse("proposal_create", args=[self.ad2.pk]),
            {
                "ad_sender": self.ad1.pk,
                "ad_receiver": self.ad2.pk,
                "comment": "Обменяю на велосипед",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.assertTrue(
            ExchangeProposal.objects.filter(
                ad_sender=self.ad1, ad_receiver=self.ad2
            ).exists()
        )

    def test_proposal_create_self(self):
        self.client.login(username="user1", password="pass1")
        response = self.client.post(
            reverse("proposal_create", args=[self.ad1.pk]),
            {
                "ad_sender": self.ad1.pk,
                "ad_receiver": self.ad1.pk,
                "comment": "Обменяю сам с собой",
            },
        )
        self.assertRedirects(response, reverse("ad_list"))
        self.assertFalse(
            ExchangeProposal.objects.filter(
                ad_sender=self.ad1, ad_receiver=self.ad1
            ).exists()
        )

    def test_proposal_list(self):
        ExchangeProposal.objects.create(
            ad_sender=self.ad1, ad_receiver=self.ad2, comment="Тест", status="pending"
        )
        self.client.login(username="user1", password="pass1")
        response = self.client.get(reverse("proposal_list"))
        self.assertContains(response, "Тест")

    def test_proposal_update_status(self):
        proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1, ad_receiver=self.ad2, comment="Тест", status="pending"
        )
        self.client.login(username="user2", password="pass2")
        response = self.client.post(
            reverse("proposal_update_status", args=[proposal.pk]),
            {"status": "accepted"},
        )
        self.assertRedirects(response, reverse("proposal_list"))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "accepted")

    def test_proposal_update_status_no_permission(self):
        proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1, ad_receiver=self.ad2, comment="Тест", status="pending"
        )
        self.client.login(username="user1", password="pass1")
        response = self.client.post(
            reverse("proposal_update_status", args=[proposal.pk]),
            {"status": "accepted"},
        )
        self.assertRedirects(response, reverse("proposal_list"))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "pending")
