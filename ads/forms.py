from django import forms
from .models import Ad, ExchangeProposal
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ["title", "description", "image", "category", "condition"]


class ExchangeProposalForm(forms.ModelForm):
    class Meta:
        model = ExchangeProposal
        fields = ["ad_sender", "ad_receiver", "comment"]


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "password1", "password2")
