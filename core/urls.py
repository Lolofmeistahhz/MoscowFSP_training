from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import YandexGeocoderView, NotificationsViewSet, YandexGeocoderViewIDs, RecordView, \
    CalendarSportInfoView, DisciplineFilterUniqueListViewJSON, DisciplineFilterUniqueListView, \
    DisciplineFilterSearchView, CalendarSportInfoStatsView

router = DefaultRouter()
router.register(r'notifications', NotificationsViewSet)

urlpatterns = [
    path('geocode', YandexGeocoderView.as_view(), name='geocode'),
    path('geocode-ids', YandexGeocoderViewIDs.as_view(), name='geocode-ids'),
    path('record', RecordView.as_view(), name='record'),
    path('calendar-sport-info', CalendarSportInfoView.as_view(), name='calendar-sport-info'),
    path('notifications', NotificationsViewSet.as_view({'get': 'list', 'post': 'create'}), name='notifications-list'),
    path('notifications/<int:pk>', NotificationsViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='notifications-detail'),
    path('discipline-filters-json', DisciplineFilterUniqueListViewJSON.as_view(), name='discipline-filter-list-JSON'),
    path('discipline-filters', DisciplineFilterUniqueListView.as_view(), name='discipline-filter-list'),
    path('discipline-filters/<str:discipline_name>/', DisciplineFilterSearchView.as_view(),
         name='discipline-filter-search'),
    path('calendar-sport-info/stats', CalendarSportInfoStatsView.as_view(), name='calendar-sport-info-stats'),
]
