from django.shortcuts import render
from django.http import JsonResponse
from .forms import SafetyPlaceForm
from .models import SafetyPlace
from datetime import datetime
from django.forms.models import model_to_dict
import json


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

            serialized_place = {
                "id": place.id,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "comment": place.comment,
                "user": place.user.username,
                "created_at": place.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }

            return JsonResponse(serialized_place)
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)