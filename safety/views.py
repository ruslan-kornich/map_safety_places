from django.shortcuts import render, get_object_or_404
from django.core import serializers
from .forms import SafetyPlaceForm
from rest_framework import viewsets
from .serializers import SafetyPlaceSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SafetyPlace
from django.contrib.auth.decorators import login_required
from accounts.models import User
from django.http import JsonResponse

from django.core import serializers
import json


def map_view(request):
    if request.method == "POST":
        if request.user.is_authenticated:
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
            return JsonResponse(
                {"error": "You must be logged in to create a place"}, status=403
            )
    else:
        places = SafetyPlace.objects.select_related("user").all()

        places_with_username = []
        for place in places:
            user_id = place.user_id
            user = User.objects.get(id=user_id)
            username = user.username
            place.user_id = username  # Обновляем поле user_id в объекте place
            places_with_username.append(place)

        places_json = serializers.serialize("json", places_with_username)
        user_authenticated = request.user.is_authenticated
        return render(
            request,
            "safety/map.html",
            {
                "places_json": places_json,
                "user_authenticated": user_authenticated,
            },
        )


@login_required
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
                "created_at": place.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }

            return JsonResponse(serialized_place)
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


class SafetyPlaceViewSet(viewsets.ModelViewSet):
    queryset = SafetyPlace.objects.all()
    serializer_class = SafetyPlaceSerializer


@login_required
@csrf_exempt
def update_place(request, place_id):
    if request.method == "POST":
        place = get_object_or_404(SafetyPlace, pk=place_id)

        if request.user != place.user and not request.user.is_superuser:
            response = JsonResponse(
                {"error": "Тільки творець цього коментаря може його редагувати."}
            )
            response.status_code = 403
            return response

        comment = request.POST.get("comment")
        place.comment = comment
        place.save()
        return JsonResponse({"comment": comment})

    else:
        return JsonResponse({"error": "Невірний запит"})


@login_required
@csrf_exempt
def delete_place(request, place_id):
    if request.method == "POST":
        place = get_object_or_404(SafetyPlace, pk=place_id)

        if request.user != place.user and not request.user.is_superuser:
            response = JsonResponse(
                {"error": "Тільки творець цього коментаря може його видалити"}
            )
            response.status_code = 403
            return response

        place.delete()
        return JsonResponse({"success": True})

    else:
        return JsonResponse({"error": "Невірний запит"})


from django.http import JsonResponse
from django.views import View
from .models import SafetyPlace


class GetDataView(View):
    def get(self, request, *args, **kwargs):
        north_east_lat = self.request.GET.get("north_east_lat")
        north_east_lng = self.request.GET.get("north_east_lng")
        south_west_lat = self.request.GET.get("south_west_lat")
        south_west_lng = self.request.GET.get("south_west_lng")

        places = SafetyPlace.objects.filter(
            latitude__lte=north_east_lat,
            latitude__gte=south_west_lat,
            longitude__lte=north_east_lng,
            longitude__gte=south_west_lng,
        )

        data = []
        for place in places:
            data.append(
                {
                    "id": place.id,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "comment": place.comment,
                    "user": place.user.username,
                    "created_at": place.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return JsonResponse(data, safe=False)
