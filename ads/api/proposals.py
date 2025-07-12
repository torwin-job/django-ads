from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ads.models import ExchangeProposal
from ads.serializers import ExchangeProposalSerializer
from ads.services import proposals as proposal_services
from typing import Any


# ViewSet для работы с предложениями обмена через API
class ExchangeProposalViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeProposalSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> Any:
        # Получает список предложений обмена для текущего пользователя с фильтрацией
        user = self.request.user
        status_param = str(self.request.query_params.get("status", "") or "")
        query = str(self.request.query_params.get("q", "") or "")
        if user.is_authenticated:
            return proposal_services.search_proposals(user, status_param, query)
        return ExchangeProposal.objects.none()

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def set_status(self, request, pk=None):
        # Изменяет статус предложения обмена (только для авторизованных пользователей)
        new_status = request.data.get("status")
        user = request.user
        if pk is None or pk == "None" or new_status is None:
            return Response(
                {"error": "Не передан id или статус"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok = proposal_services.atomic_update_proposal_status(
            int(pk), user, str(new_status)
        )
        if ok:
            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Недостаточно прав или неверный статус"},
            status=status.HTTP_400_BAD_REQUEST,
        )
