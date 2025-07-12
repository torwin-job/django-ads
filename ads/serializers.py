from rest_framework import serializers
from .models import Ad, ExchangeProposal


class AdSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ad
        fields = "__all__"


class ExchangeProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeProposal
        fields = "__all__"
