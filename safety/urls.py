from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import SafetyPlaceViewSet, map_view, create_place, update_place, delete_place

router = DefaultRouter()
router.register('safetyplaces', SafetyPlaceViewSet)

urlpatterns = [
    path("", map_view, name="map"),
    path("create/", create_place, name="create_place"),
    path('update/<int:place_id>/', update_place, name='update_place'),
    path('delete/<int:place_id>/', delete_place, name='delete_place'),
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
