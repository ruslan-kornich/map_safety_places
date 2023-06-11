from django.shortcuts import render
from django.core import serializers
from .forms import SafetyPlaceForm
from rest_framework import viewsets
from .serializers import SafetyPlaceSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SafetyPlace
from django.contrib.auth.decorators import login_required

def map_view(request):
    if request.method == 'POST':
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
            return JsonResponse({"error": "You must be logged in to create a place"}, status=403)
    else:
        form = SafetyPlaceForm()
        places = SafetyPlace.objects.all()
        places_json = serializers.serialize('json', places)
        user_authenticated = request.user.is_authenticated
        return render(request, "safety/map.html", {"form": form, "places_json": places_json, 'user_authenticated': user_authenticated})


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
                "created_at": place.created_at.strftime("%Y-%m-%d %H:%M:%S")
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
    if request.method == 'POST':
        data = request.POST
        comment = data.get('comment', None)
        if comment is not None:
            SafetyPlace.objects.filter(id=place_id).update(comment=comment)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error'}, status=400)

@login_required
@csrf_exempt
def delete_place(request, place_id):
    if request.method == 'POST':
        SafetyPlace.objects.filter(id=place_id).delete()
        return JsonResponse({'status': 'success'})
