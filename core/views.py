import os

import requests
from django.core.mail import send_mail
from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets

from utils import send_telegram_message
from .models import Notifications, CalendarSportInfo
from .serializers import GeocodeSerializer, NotificationsSerializer, CalendarSportInfoIdsSerializer, RecordSerializer


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
    def post(self, request):
        serializer = RecordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)