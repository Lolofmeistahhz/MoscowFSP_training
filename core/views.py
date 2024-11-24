import datetime
import json
import logging

import requests
from django.db import transaction
from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, generics

from .models import Notifications, CalendarSportInfo, DisciplineFilter
from .serializers import GeocodeSerializer, NotificationsSerializer, CalendarSportInfoIdsSerializer, RecordSerializer, \
    CalendarSportInfoSerializer, CalendarSportInfoFilterSerializer, DisciplineFilterSerializer, EmptySerializer

logger = logging.getLogger(__name__)


class YandexGeocoderView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('address', openapi.IN_QUERY, description="Address to geocode", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response('Geocoding successful', GeocodeSerializer),
            400: 'Invalid address',
            404: 'Address not found',
            500: 'Internal server error'
        }
    )
    def get(self, request):
        serializer = GeocodeSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        address = serializer.validated_data['address']

        api_key = 'c4db6524-be53-4158-8b78-08b74c610458'

        url = f'https://geocode-maps.yandex.ru/1.x/?format=json&apikey={api_key}&geocode={address}'

        try:
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            geo_objects = data['response']['GeoObjectCollection']['featureMember']
            if geo_objects:
                coordinates = geo_objects[0]['GeoObject']['Point']['pos']
                latitude, longitude = map(float, coordinates.split(' '))
                return_data = {'address': address, 'latitude': latitude, 'longitude': longitude}
                return Response(return_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class YandexGeocoderViewIDs(APIView):
    @swagger_auto_schema(
        request_body=CalendarSportInfoIdsSerializer,
        responses={
            200: openapi.Response('Geocoding successful', CalendarSportInfoIdsSerializer),
            400: 'Invalid data',
            404: 'Address not found',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        serializer = CalendarSportInfoIdsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data['ids']
        api_key = 'c4db6524-be53-4158-8b78-08b74c610458'
        coordinates_list = []

        for id in ids:
            try:
                calendar_sport_info = CalendarSportInfo.objects.get(id=id)
                address = calendar_sport_info.location
                url = f'https://geocode-maps.yandex.ru/1.x/?format=json&apikey={api_key}&geocode={address}'

                response = requests.get(url)
                response.raise_for_status()

                data = response.json()
                geo_objects = data['response']['GeoObjectCollection']['featureMember']
                if geo_objects:
                    coordinates = geo_objects[0]['GeoObject']['Point']['pos']
                    latitude, longitude = map(float, coordinates.split(' '))
                    coordinates_list.append({
                        'id': id,
                        'address': address,
                        'latitude': latitude,
                        'longitude': longitude
                    })
                else:
                    coordinates_list.append({
                        'id': id,
                        'address': address,
                        'error': 'Address not found'
                    })
            except CalendarSportInfo.DoesNotExist:
                coordinates_list.append({
                    'id': id,
                    'error': 'CalendarSportInfo not found'
                })
            except requests.exceptions.RequestException as e:
                coordinates_list.append({
                    'id': id,
                    'address': address,
                    'error': str(e)
                })

        return Response(coordinates_list, status=status.HTTP_200_OK)


class NotificationsViewSet(viewsets.ModelViewSet):
    queryset = Notifications.objects.all()
    serializer_class = NotificationsSerializer

class RecordView(APIView):
    @swagger_auto_schema(
        request_body=RecordSerializer,
        responses={
            201: openapi.Response('Created', RecordSerializer),
            400: 'Invalid data'
        }
    )
    def post(self, request, format=None):
        try:
            if isinstance(request.data, list):
                serializer = RecordSerializer(data=request.data, many=True)
            else:
                serializer = RecordSerializer(data=request.data)

            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                logger.info("Data successfully saved.")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Invalid data: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def is_overlap(booking1, booking2):
    start1, end1 = booking1['date_from'], booking1['date_to']
    start2, end2 = booking2['date_from'], booking2['date_to']
    return not (end1 < start2 or end2 < start1)


def filter_bookings(bookings):
    sorted_bookings = sorted(bookings, key=lambda x: x['date_from'])

    result = []
    for booking in sorted_bookings:
        if all(not is_overlap(booking, b) for b in result):
            result.append(booking)

    return result


class CalendarSportInfoView(APIView):
    @swagger_auto_schema(
        request_body=CalendarSportInfoFilterSerializer,
        responses={
            200: openapi.Response('Filtered CalendarSportInfo', CalendarSportInfoSerializer(many=True)),
            400: 'Invalid data'
        }
    )
    def post(self, request):
        filter_serializer = CalendarSportInfoFilterSerializer(data=request.data)

        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data

            queryset = CalendarSportInfo.objects.all()

            if filters.get('calendarSportId'):
                queryset = queryset.filter(calendar_sport__id__in=filters['calendarSportId'])
            if filters.get('disciplineId'):
                queryset = queryset.filter(disciplinefilter__discipline__id__in=filters['disciplineId'])
            if filters.get('programId'):
                queryset = queryset.filter(programfilter__program__id__in=filters['programId'])
            if filters.get('location') is not None:
                queryset = queryset.filter(location__icontains=filters['location'])
            if filters.get('minCount') is not None:
                queryset = queryset.filter(count__gte=filters['minCount'])
            if filters.get('maxCount') is not None:
                queryset = queryset.filter(count__lte=filters['maxCount'])
            if filters.get('ageId'):
                queryset = queryset.filter(sexagefilter__age__id__in=filters['ageId'])
            if filters.get('sexId'):
                queryset = queryset.filter(sexagefilter__sex__id__in=filters['sexId'])
            if filters.get('dateFrom') is not None:
                queryset = queryset.filter(date_from__gte=filters['dateFrom'])
            if filters.get('dateTo') is not None:
                queryset = queryset.filter(date_to__lte=filters['dateTo'])
            if filters.get('calendarSportTypeId'):
                queryset = queryset.filter(calendar_sport_type__id__in=filters['calendarSportTypeId'])

            bookings = [
                {
                    'id': item.id,
                    'date_from': item.date_from,
                    'date_to': item.date_to
                }
                for item in queryset
            ]

            filtered_bookings = filter_bookings(bookings)

            filtered_ids = [booking['id'] for booking in filtered_bookings]
            filtered_queryset = CalendarSportInfo.objects.filter(id__in=filtered_ids)

            paginator = PageNumberPagination()
            paginator.page_size = filters.get('size', 10)
            paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)

            result_serializer = CalendarSportInfoSerializer(paginated_queryset, many=True)

            return paginator.get_paginated_response(result_serializer.data)
        else:
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisciplineFilterUniqueListView(generics.ListAPIView):
    serializer_class = DisciplineFilterSerializer

    def get_queryset(self):
        return DisciplineFilter.objects.all()

    def list(self, request, *args, **kwargs):
        chunk_size = 1000
        unique_entries = set()

        for chunk in self.get_queryset().values('discipline__id', 'discipline__name').iterator(chunk_size=chunk_size):
            entry = {'id': chunk['discipline__id'], 'name': chunk['discipline__name']}
            unique_entries.add(frozenset(entry.items()))

        unique_entries_list = [dict(entry) for entry in unique_entries]
        return Response(unique_entries_list)


class DisciplineFilterSearchView(generics.GenericAPIView):
    serializer_class = DisciplineFilterSerializer

    def get(self, request):
        discipline_name = request.query_params.get('name', '')

        if not discipline_name:
            return Response({'error': 'Name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        chunk_size = 1000
        unique_entries = set()

        queryset = DisciplineFilter.objects.filter(discipline__name__icontains=discipline_name)
        for chunk in queryset.values('discipline__id', 'discipline__name').iterator(chunk_size=chunk_size):
            entry = {'id': chunk['discipline__id'], 'name': chunk['discipline__name']}
            unique_entries.add(frozenset(entry.items()))

        unique_entries_list = [dict(entry) for entry in unique_entries]

        return Response(unique_entries_list)

class DisciplineFilterUniqueListViewJSON(generics.ListAPIView):
    serializer_class = DisciplineFilterSerializer

    def get_queryset(self):
        return DisciplineFilter.objects.all()

    def list(self, request, *args, **kwargs):
        chunk_size = 1000
        unique_entries = set()

        for chunk in self.get_queryset().values('discipline__id', 'discipline__name').iterator(chunk_size=chunk_size):
            entry = {'id': chunk['discipline__id'], 'name': chunk['discipline__name']}
            unique_entries.add(frozenset(entry.items()))

        unique_entries_list = [dict(entry) for entry in unique_entries]

        with open('result.json', 'w') as f:
            json.dump(unique_entries_list, f)

        with open('result.json', 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="result.json"'
            return response

class CalendarSportInfoStatsView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    def get(self, request, *args, **kwargs):
        now = datetime.datetime.now()

        total_events = CalendarSportInfo.objects.count()

        past_events = CalendarSportInfo.objects.filter(date_to__lt=now).count()


        past_percentage = (past_events / total_events) * 100 if total_events > 0 else 0

        future_percentage = 100 - past_percentage

        result = [past_percentage, total_events, future_percentage]

        return Response(result)