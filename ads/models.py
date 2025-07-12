from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class Ad(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(
        upload_to="ads/", blank=True, null=True, verbose_name="Изображение"
    )
    category = models.CharField(max_length=100, verbose_name="Категория")
    condition = models.CharField(max_length=50, verbose_name="Состояние")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    objects = models.Manager()

    def __str__(self):
        return self.title


class ExchangeProposal(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("accepted", "Принята"),
        ("rejected", "Отклонена"),
    ]
    ad_sender = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name="sent_proposals",
        verbose_name="Объявление отправителя",
    )
    ad_receiver = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name="received_proposals",
        verbose_name="Объявление получателя",
    )
    comment = models.TextField(verbose_name="Комментарий")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    objects = models.Manager()

    def __str__(self):
        status_display = dict(self.STATUS_CHOICES).get(str(self.status), self.status)
        return f"{self.ad_sender} → {self.ad_receiver} ({status_display})"
