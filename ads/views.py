from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ad
from .forms import AdForm, ExchangeProposalForm, RegisterForm
from django.core.paginator import Paginator
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from ads.services.ads import search_ads, get_ads_indicators, get_user_exchange_map
from ads.services.proposals import search_proposals, atomic_update_proposal_status


# Список объявлений с поиском и фильтрацией
def ad_list(request):
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    condition = request.GET.get("condition", "")
    ads = search_ads(query, category, condition)
    paginator = Paginator(ads, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    incoming, outgoing = get_ads_indicators(page_obj, request.user)
    exchange_map = get_user_exchange_map(page_obj, request.user)
    return render(
        request,
        "ads/ad_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "category": category,
            "condition": condition,
            "incoming": incoming,
            "outgoing": outgoing,
            "exchange_map": exchange_map,
        },
    )


# Создание объявления
@login_required
def ad_create(request):
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            messages.success(request, "Объявление успешно создано!")
            return redirect("ad_list")
    else:
        form = AdForm()
    return render(request, "ads/ad_form.html", {"form": form})


# Редактирование объявления
@login_required
def ad_edit(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if ad.user != request.user:
        messages.error(request, "Вы не являетесь автором этого объявления!")
        return redirect("ad_list")
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, "Объявление обновлено!")
            return redirect("ad_list")
    else:
        form = AdForm(instance=ad)
    return render(request, "ads/ad_form.html", {"form": form, "edit": True})


# Удаление объявления
@login_required
def ad_delete(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if ad.user != request.user:
        messages.error(request, "Вы не являетесь автором этого объявления!")
        return redirect("ad_list")
    if request.method == "POST":
        ad.delete()
        messages.success(request, "Объявление удалено!")
        return redirect("ad_list")
    return render(request, "ads/ad_confirm_delete.html", {"ad": ad})


# Создание предложения обмена
@login_required
def proposal_create(request, ad_receiver_id):
    ad_receiver = get_object_or_404(Ad, pk=ad_receiver_id)
    user_ads = Ad.objects.filter(user=request.user)
    # Запретить предлагать обмен самому себе
    if ad_receiver.user == request.user:
        messages.error(
            request, "Вы не можете предлагать обмен своему собственному объявлению!"
        )
        return redirect("ad_list")
    if request.method == "POST":
        form = ExchangeProposalForm(request.POST)
        form.fields["ad_sender"].queryset = user_ads
        form.fields["ad_receiver"].queryset = Ad.objects.filter(pk=ad_receiver_id)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.status = "pending"
            proposal.save()
            messages.success(request, "Предложение отправлено!")
            return redirect("ad_list")
    else:
        form = ExchangeProposalForm()
        form.fields["ad_sender"].queryset = user_ads
        form.fields["ad_receiver"].queryset = Ad.objects.filter(pk=ad_receiver_id)
    return render(
        request, "ads/proposal_form.html", {"form": form, "ad_receiver": ad_receiver}
    )


# Список предложений (фильтрация по пользователю и статусу)
@login_required
def proposal_list(request):
    status = request.GET.get("status", "")
    query = request.GET.get("q", "")
    proposals = search_proposals(request.user, status, query)
    paginator = Paginator(proposals, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request, "ads/proposal_list.html", {"page_obj": page_obj, "status": status}
    )


@login_required
@require_POST
def proposal_update_status(request, pk):
    new_status = request.POST.get("status")
    ok = atomic_update_proposal_status(pk, request.user, new_status)
    if ok:
        messages.success(request, "Статус предложения изменён!")
    else:
        messages.error(
            request, "Ошибка: вы не можете менять статус или недопустимый статус!"
        )
    return redirect("proposal_list")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("ad_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
