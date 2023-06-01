from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import SafetyPlaceForm
from .models import SafetyPlace
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework_gis.serializers import GeoModelSerializer

from django.shortcuts import render
from django.http import JsonResponse
from .forms import SafetyPlaceForm
from .models import SafetyPlace


def map_view(request):
    if request.method == "POST":
        form = SafetyPlaceForm(request.POST)
        if form.is_valid():
            place = form.save(commit=False)
            place.user = request.user
            place.save()
            return JsonResponse(
                {
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "comment": place.comment,
                }
            )
    else:
        form = SafetyPlaceForm()
    places = SafetyPlace.objects.all()
    return render(request, "safety/map.html", {"form": form, "places": places})


def create_place(request):
    if request.method == "POST":
        form = SafetyPlaceForm(request.POST)
        if form.is_valid():
            place = form.save(commit=False)
            place.user = request.user
            place.save()
            return JsonResponse(
                {
                    "id": place.id,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "comment": place.comment,
                }
            )
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
