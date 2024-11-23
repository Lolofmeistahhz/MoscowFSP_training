import os
from concurrent.futures import ThreadPoolExecutor

from rest_framework import serializers

from core.models import Notifications, SexCategory, AgeCategory, CalendarSportType, TeamInfo, CalendarSportInfo, \
    SexAgeFilter, ProgramInfo, ProgramFilter, DisciplineInfo, DisciplineFilter, CalendarSport, Calendar


class GeocodeSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=255, required=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)


class CalendarSportInfoIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ['id', 'name', 'event_info', 'calendar_sport_info', 'user']


class GenderAgeSerializer(serializers.Serializer):
    gender = serializers.CharField()
    minAge = serializers.IntegerField(allow_null=True)
    maxAge = serializers.IntegerField(allow_null=True)

    def create(self, validated_data):
        gender = validated_data['gender']
        minAge = validated_data['minAge']
        maxAge = validated_data['maxAge']

        sex_category, _ = SexCategory.objects.get_or_create(sex=gender)

        # Обработка случая, когда minAge или maxAge равны null
        if minAge is None and maxAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age="")
        elif minAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age=f"-{maxAge}")
        elif maxAge is None:
            age_category, _ = AgeCategory.objects.get_or_create(age=f"{minAge}-")
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
    calendar = serializers.CharField(write_only=True, required=False)  # Добавлено новое поле

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
            calendar_name = validated_data.pop('calendar', None)  # Добавлено новое поле

            # Извлекаем значение name из validated_data
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

            def create_sex_age_filter(gender_age):
                try:
                    gender_age_serializer = GenderAgeSerializer(data=gender_age)
                    if gender_age_serializer.is_valid():
                        gender_age_instance = gender_age_serializer.save()
                        sex_category = gender_age_instance['sex_category']
                        age_category = gender_age_instance['age_category']
                        SexAgeFilter.objects.create(
                            sex=sex_category,
                            age=age_category,
                            calendar_sport_info=calendar_sport_info
                        )
                    else:
                        print(f"GenderAgeSerializer validation error: {gender_age_serializer.errors}")
                        raise serializers.ValidationError(gender_age_serializer.errors)
                except Exception as e:
                    print(f"Error creating SexAgeFilter: {e}")

            def create_program_filter(program_name):
                try:
                    program, _ = ProgramInfo.objects.get_or_create(name=program_name)
                    ProgramFilter.objects.create(
                        program=program,
                        calendar_sport_info=calendar_sport_info
                    )
                except Exception as e:
                    print(f"Error creating ProgramFilter: {e}")

            def create_discipline_filter(discipline_name):
                try:
                    discipline, _ = DisciplineInfo.objects.get_or_create(name=discipline_name)
                    DisciplineFilter.objects.create(
                        discipline=discipline,
                        calendar_sport_info=calendar_sport_info
                    )
                except Exception as e:
                    print(f"Error creating DisciplineFilter: {e}")

            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(create_sex_age_filter, gender_age_data)
                executor.map(create_program_filter, programms_data)
                executor.map(create_discipline_filter, disciplines_data)

            return calendar_sport_info
        except Exception as e:
            print(f"An error occurred in RecordSerializer.create: {e}")
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
