from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import YandexGeocoderView, NotificationsViewSet, YandexGeocoderViewIDs, RecordView

router = DefaultRouter()
router.register(r'notifications', NotificationsViewSet)

urlpatterns = [
    path('geocode/', YandexGeocoderView.as_view(), name='geocode'),
    path('geocode-ids/', YandexGeocoderViewIDs.as_view(), name='geocode-ids'),
    path('record/', RecordView.as_view(), name='record'),
    path('', include(router.urls))
]
