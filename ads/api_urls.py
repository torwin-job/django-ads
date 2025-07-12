from rest_framework.routers import DefaultRouter
from ads.api.ads import AdViewSet
from ads.api.proposals import ExchangeProposalViewSet
from ads.api.auth import RegisterView, LogoutView
from django.urls import path

router = DefaultRouter()
router.register(r"ads", AdViewSet, basename="ad")
router.register(r"proposals", ExchangeProposalViewSet, basename="exchangeproposal")

urlpatterns = router.urls
urlpatterns += [
    path("register/", RegisterView.as_view(), name="api_register"),
    path("logout/", LogoutView.as_view(), name="api_logout"),
]
