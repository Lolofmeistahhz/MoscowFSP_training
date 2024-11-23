import os

import requests
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets

from utils import send_telegram_message
from .models import Notifications, CalendarSportInfo
from .serializers import GeocodeSerializer, NotificationsSerializer, CalendarSportInfoIdsSerializer, RecordSerializer, \
    CalendarSportInfoSerializer, CalendarSportInfoFilterSerializer


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
                send_telegram_message(message=f'Вот что вы искали {address}', chat_id='2108938640')
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
        if isinstance(request.data, list):
            serializer = RecordSerializer(data=request.data, many=True)
        else:
            serializer = RecordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def is_overlap(booking1, booking2):
    """Проверяет, пересекаются ли две заявки."""
    start1, end1 = booking1['date_from'], booking1['date_to']
    start2, end2 = booking2['date_from'], booking2['date_to']
    return not (end1 < start2 or end2 < start1)


def filter_bookings(bookings):
    """Фильтрует заявки, оставляя только те, которые не пересекаются."""
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
