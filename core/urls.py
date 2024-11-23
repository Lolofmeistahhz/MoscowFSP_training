from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import YandexGeocoderView, NotificationsViewSet, YandexGeocoderViewIDs, RecordView, \
    CalendarSportInfoView
router = DefaultRouter()
router.register(r'notifications', NotificationsViewSet)

urlpatterns = [
    path('geocode/', YandexGeocoderView.as_view(), name='geocode'),
    path('geocode-ids/', YandexGeocoderViewIDs.as_view(), name='geocode-ids'),
    path('record/', RecordView.as_view(), name='record'),
    path('calendar-sport-info/', CalendarSportInfoView.as_view(), name='calendar-sport-info'),
    path('', include(router.urls))
]
