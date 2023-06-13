from rest_framework import serializers, viewsets
from .models import SafetyPlace


class SafetyPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyPlace
        fields = ["id", "user", "latitude", "longitude", "comment", "created_at"]
