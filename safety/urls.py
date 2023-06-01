from django.urls import path

from .views import map_view

app_name = 'safety'

urlpatterns = [
    path('', map_view, name='home'),
]
