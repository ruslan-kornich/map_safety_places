from django import forms
from .models import SafetyPlace


class SafetyPlaceForm(forms.ModelForm):
    class Meta:
        model = SafetyPlace
        fields = ["latitude", "longitude", "comment"]
