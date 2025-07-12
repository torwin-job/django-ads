from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ads.models import Ad
from ads.serializers import AdSerializer
from ads.services import ads as ads_services
from typing import Any

# ViewSet для работы с объявлениями через API
class AdViewSet(viewsets.ModelViewSet):
    serializer_class = AdSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> Any:
        # Получает список объявлений с фильтрацией по запросу, категории и состоянию
        query = str(self.request.query_params.get("q", "") or "")
        category = str(self.request.query_params.get("category", "") or "")
        condition = str(self.request.query_params.get("condition", "") or "")
        return ads_services.search_ads(query, category, condition)

    def perform_create(self, serializer):
        # Сохраняет объявление с текущим пользователем как владельцем
        serializer.save(user=self.request.user)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def exchange_indicators(self, request):
        # Возвращает индикаторы обмена для списка объявлений
        ad_ids = request.data.get("ad_ids", [])
        if not isinstance(ad_ids, list) or not all(isinstance(i, int) for i in ad_ids):
            return Response(
                {"error": "Передайте список id объявлений (ad_ids)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ads = Ad.objects.filter(pk__in=ad_ids)
        incoming, outgoing = ads_services.get_ads_indicators(ads, request.user)
        exchange_map = ads_services.get_user_exchange_map(ads, request.user)
        return Response(
            {
                "incoming": incoming,
                "outgoing": list(outgoing),
                "exchange_map": exchange_map,
            }
        )
