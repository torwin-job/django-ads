from functools import reduce
import operator
from typing import Tuple, Dict, Set, Any
from django.db.models import Q, QuerySet, Count
from django.contrib.auth.models import AbstractBaseUser
from ads.models import Ad, ExchangeProposal


def search_ads(query: str, category: str, condition: str) -> QuerySet:
    """
    Поиск объявлений по всем основным полям (нечувствительно к регистру).
    :param query: поисковый запрос
    :param category: фильтр по категории
    :param condition: фильтр по состоянию
    :return: QuerySet объявлений
    """
    ads = Ad.objects.all().order_by("-created_at")
    ads = ads.select_related("user").prefetch_related("received_proposals")
    if query:
        q_list = [
            Q(title__icontains=query),
            Q(description__icontains=query),
            Q(category__icontains=query),
            Q(condition__icontains=query),
            Q(user__username__icontains=query),
        ]
        ads = ads.filter(reduce(operator.or_, q_list))
    if category:
        ads = ads.filter(category__iexact=category)
    if condition:
        ads = ads.filter(condition__iexact=condition)
    return ads


def get_ads_indicators(
    page_obj: Any, user: AbstractBaseUser
) -> Tuple[Dict[int, int], Set[int]]:
    """
    Возвращает индикаторы предложений обмена для объявлений на странице.
    :param page_obj: страница объявлений (Page)
    :param user: текущий пользователь
    :return: (incoming, outgoing) — словарь входящих и множество исходящих предложений
    """
    ad_ids = [ad.pk for ad in page_obj]
    incoming_counts = ExchangeProposal.objects.filter(ad_receiver_id__in=ad_ids)
    incoming_counts = incoming_counts.values("ad_receiver_id").annotate(cnt=Count("id"))
    incoming: Dict[int, int] = {
        item["ad_receiver_id"]: item["cnt"] for item in incoming_counts
    }
    outgoing: Set[int] = set()
    if user.is_authenticated:
        outgoing_qs = ExchangeProposal.objects.filter(
            ad_sender__user=user, ad_receiver_id__in=ad_ids
        )
        outgoing = set(outgoing_qs.values_list("ad_receiver_id", flat=True))
    return incoming, outgoing


def get_user_exchange_map(page_obj: Any, user: AbstractBaseUser) -> Dict[int, bool]:
    """
    Для каждого объявления на странице определяет, есть ли хотя бы одно предложение обмена между пользователем и этим объявлением (в обе стороны).
    :param page_obj: страница объявлений (Page)
    :param user: текущий пользователь
    :return: словарь ad_id -> bool (есть обмен между пользователями)
    """
    ad_ids = [ad.pk for ad in page_obj]
    exchange_map = {ad_id: False for ad_id in ad_ids}
    if user.is_authenticated:
        q_list = [
            Q(ad_sender__user=user, ad_receiver_id__in=ad_ids),
            Q(ad_receiver__user=user, ad_sender_id__in=ad_ids),
        ]
        qs = ExchangeProposal.objects.filter(reduce(operator.or_, q_list))
        for p in qs:
            if p.ad_sender_id in ad_ids:
                exchange_map[p.ad_sender_id] = True
            if p.ad_receiver_id in ad_ids:
                exchange_map[p.ad_receiver_id] = True
    return exchange_map
