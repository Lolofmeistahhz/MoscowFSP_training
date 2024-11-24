import logging

from django.db import transaction
from rest_framework import serializers

from core.models import Notifications, SexCategory, AgeCategory, CalendarSportType, TeamInfo, CalendarSportInfo, \
    SexAgeFilter, ProgramInfo, ProgramFilter, DisciplineInfo, DisciplineFilter, CalendarSport, Calendar

logger = logging.getLogger(__name__)


class GeocodeSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=255, required=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)


class CalendarSportInfoIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = "__all__"


class GenderAgeSerializer(serializers.Serializer):
    gender = serializers.CharField()
    minAge = serializers.IntegerField(allow_null=True)
    maxAge = serializers.IntegerField(allow_null=True)

    def create(self, validated_data):
        gender = validated_data['gender']
        minAge = validated_data['minAge']
        maxAge = validated_data['maxAge']

        sex_category, _ = SexCategory.objects.get_or_create(sex=gender)

        if minAge is None and maxAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age="20-45")
        elif minAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age=f"20-45")
        elif maxAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age=f"20-45")
        else:
            age_category, _ = AgeCategory.objects.get_or_create(age=f"{minAge}-{maxAge}")

        return {'sex_category': sex_category, 'age_category': age_category}


class RecordSerializer(serializers.ModelSerializer):
    sport_type = serializers.CharField(write_only=True, required=False)
    sport_type_per_person = serializers.CharField(write_only=True, required=False)
    uid = serializers.CharField(source='ekp', allow_null=True, required=False, write_only=True)
    event_name = serializers.CharField(write_only=True, required=False)
    start_date = serializers.DateField(source='date_from', write_only=True, required=False)
    end_date = serializers.DateField(source='date_to', write_only=True, required=False)
    members = serializers.IntegerField(source='count', write_only=True, required=False)
    location = serializers.CharField(write_only=True, required=False)
    genderAge = GenderAgeSerializer(many=True, required=False, write_only=True)
    programms = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    disciplines = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    calendar = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CalendarSportInfo
        fields = [
            'sport_type', 'sport_type_per_person', 'uid', 'event_name', 'start_date', 'end_date',
            'members', 'location', 'genderAge', 'programms', 'disciplines', 'calendar'
        ]

    def create(self, validated_data):
        try:
            sport_type_name = validated_data.pop('sport_type', None)
            sport_type_per_person_name = validated_data.pop('sport_type_per_person', None)
            gender_age_data = validated_data.pop('genderAge', [])
            programms_data = validated_data.pop('programms', [])
            disciplines_data = validated_data.pop('disciplines', [])
            calendar_name = validated_data.pop('calendar', None)

            name = validated_data.pop("event_name", None)

            if sport_type_name:
                sport_type, _ = CalendarSport.objects.get_or_create(name=sport_type_name)
            else:
                sport_type = None

            if name:
                sport_type_per_person, _ = CalendarSportType.objects.get_or_create(name=name)
            else:
                sport_type_per_person = None

            if calendar_name:
                calendar, _ = Calendar.objects.get_or_create(name=calendar_name)
            else:
                calendar = None

            if sport_type and calendar:
                sport_type.calendar = calendar
                sport_type.save()

            calendar_sport_info = CalendarSportInfo.objects.create(
                calendar_sport=sport_type,
                calendar_sport_type=sport_type_per_person,
                team=TeamInfo.objects.get_or_create(name=sport_type_per_person_name)[
                    0] if sport_type_per_person_name else None,
                ekp=validated_data.get('ekp'),
                description=validated_data.get('description'),
                date_from=validated_data.get('date_from'),
                date_to=validated_data.get('date_to'),
                count=validated_data.get('count'),
                location=validated_data.get('location')
            )

            sex_age_filters = []
            for gender_age in gender_age_data:
                try:
                    gender_age_serializer = GenderAgeSerializer(data=gender_age)
                    if gender_age_serializer.is_valid():
                        gender_age_instance = gender_age_serializer.save()
                        sex_category = gender_age_instance['sex_category']
                        age_category = gender_age_instance['age_category']
                        sex_age_filters.append(SexAgeFilter(
                            sex=sex_category,
                            age=age_category,
                            calendar_sport_info=calendar_sport_info
                        ))
                    else:
                        logger.error(f"GenderAgeSerializer validation error: {gender_age_serializer.errors}")
                        raise serializers.ValidationError(gender_age_serializer.errors)
                except Exception as e:
                    logger.error(f"Error creating SexAgeFilter: {e}")

            program_filters = []
            for program_name in programms_data:
                try:
                    program, _ = ProgramInfo.objects.get_or_create(name=program_name)
                    program_filters.append(ProgramFilter(
                        program=program,
                        calendar_sport_info=calendar_sport_info
                    ))
                except Exception as e:
                    logger.error(f"Error creating ProgramFilter: {e}")

            discipline_filters = []
            for discipline_name in disciplines_data:
                try:
                    discipline, _ = DisciplineInfo.objects.get_or_create(name=discipline_name)
                    discipline_filters.append(DisciplineFilter(
                        discipline=discipline,
                        calendar_sport_info=calendar_sport_info
                    ))
                except Exception as e:
                    logger.error(f"Error creating DisciplineFilter: {e}")

            with transaction.atomic():
                SexAgeFilter.objects.bulk_create(sex_age_filters)
                ProgramFilter.objects.bulk_create(program_filters)
                DisciplineFilter.objects.bulk_create(discipline_filters)

            return calendar_sport_info
        except Exception as e:
            logger.error(f"An error occurred in RecordSerializer.create: {e}")
            raise


class CalendarSportInfoFilterSerializer(serializers.Serializer):
    calendarSportId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    disciplineId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    programId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    location = serializers.CharField(required=False, allow_null=True)
    minCount = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    maxCount = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    ageId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    sexId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    dateFrom = serializers.DateField(required=False, allow_null=True)
    dateTo = serializers.DateField(required=False, allow_null=True)
    calendarSportTypeId = serializers.ListField(child=serializers.IntegerField(min_value=0), required=False, default=[])
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    size = serializers.IntegerField(min_value=1, required=False, default=10)


class CalendarSportInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSportInfo
        fields = '__all__'


class DisciplineFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplineFilter
        fields = '__all__'


class EmptySerializer(serializers.Serializer):
    pass