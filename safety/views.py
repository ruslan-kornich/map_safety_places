from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Place

def map_view(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        comment = request.POST.get('comment')
        place = Place(latitude=latitude, longitude=longitude, comment=comment)
        place.save()

        # Возвращаем JSON-ответ с информацией о новом месте
        return JsonResponse({'latitude': latitude, 'longitude': longitude, 'comment': comment})

    places = Place.objects.all()
    context = {'places': places}
    return render(request, 'safety/map.html', context)
