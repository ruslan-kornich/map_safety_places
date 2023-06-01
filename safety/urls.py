from django.urls import path
from .views import map_view, create_place

urlpatterns = [
    path("", map_view, name="map"),
    path("create/", create_place, name="create_place"),
]
