from django.urls import path
from . import views

urlpatterns = [
    path("", views.ad_list, name="ad_list"),
    path("ad/create/", views.ad_create, name="ad_create"),
    path("ad/<int:pk>/edit/", views.ad_edit, name="ad_edit"),
    path("ad/<int:pk>/delete/", views.ad_delete, name="ad_delete"),
    path(
        "proposal/create/<int:ad_receiver_id>/",
        views.proposal_create,
        name="proposal_create",
    ),
    path("proposals/", views.proposal_list, name="proposal_list"),
    path(
        "proposal/<int:pk>/status/",
        views.proposal_update_status,
        name="proposal_update_status",
    ),
    path("register/", views.register, name="register"),
]
