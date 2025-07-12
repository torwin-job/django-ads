from functools import reduce
import operator
from django.db.models import Q, QuerySet
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from ads.models import ExchangeProposal


def search_proposals(user: AbstractBaseUser, status: str, query: str) -> QuerySet:
    """
    Поиск и фильтрация предложений обмена по всем основным полям.
    :param user: текущий пользователь
    :param status: фильтр по статусу
    :param query: поисковый запрос
    :return: QuerySet предложений обмена
    """
    proposals = ExchangeProposal.objects.filter(
        Q(ad_sender__user=user) | Q(ad_receiver__user=user)
    ).order_by("-created_at")
    proposals = proposals.select_related(
        "ad_sender", "ad_receiver", "ad_sender__user", "ad_receiver__user"
    )
    if status:
        proposals = proposals.filter(status=status)
    if query:
        q_list = [
            Q(ad_sender__title__icontains=query),
            Q(ad_sender__description__icontains=query),
            Q(ad_sender__category__icontains=query),
            Q(ad_sender__condition__icontains=query),
            Q(ad_sender__user__username__icontains=query),
            Q(ad_receiver__title__icontains=query),
            Q(ad_receiver__description__icontains=query),
            Q(ad_receiver__category__icontains=query),
            Q(ad_receiver__condition__icontains=query),
            Q(ad_receiver__user__username__icontains=query),
            Q(comment__icontains=query),
        ]
        proposals = proposals.filter(reduce(operator.or_, q_list))
    return proposals


@transaction.atomic
def atomic_update_proposal_status(
    proposal_id: int, user: AbstractBaseUser, status: str
) -> bool:
    """
    Атомарно обновляет статус предложения обмена, если пользователь — получатель.
    :param proposal_id: id предложения
    :param user: текущий пользователь
    :param status: новый статус ('accepted' или 'rejected')
    :return: True, если статус изменён, иначе False
    """
    try:
        proposal = ExchangeProposal.objects.select_for_update().get(pk=proposal_id)
        if proposal.ad_receiver.user != user:
            return False
        if status in dict(ExchangeProposal.STATUS_CHOICES):
            proposal.status = status
            proposal.save()
            return True
        return False
    except Exception:
        return False
