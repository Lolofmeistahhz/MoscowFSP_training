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
    sport_type = serializers.CharField(write_only=True)
    sport_type_person_type = serializers.CharField(write_only=True)
    uid = serializers.CharField(source='ekp', allow_null=True, required=False, write_only=True)
    event_name = serializers.CharField(write_only=True)
    start_date = serializers.DateField(source='date_from', write_only=True)
    end_date = serializers.DateField(source='date_to', write_only=True)
    members = serializers.IntegerField(source='count', write_only=True)
    location = serializers.CharField(write_only=True)
    metadata = serializers.CharField(source='description', write_only=True)
    genderAge = GenderAgeSerializer(many=True, required=False, write_only=True)
    programms = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    disciplines = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    calendar = serializers.CharField(write_only=True)  # Добавлено новое поле

    class Meta:
        model = CalendarSportInfo
        fields = [
            'sport_type', 'sport_type_person_type', 'uid', 'event_name', 'start_date', 'end_date',
            'members', 'location', 'metadata', 'genderAge', 'programms', 'disciplines', 'calendar'
        ]

    def create(self, validated_data):
        sport_type_name = validated_data.pop('sport_type')
        sport_type_person_type_name = validated_data.pop('sport_type_person_type')
        gender_age_data = validated_data.pop('genderAge', [])
        programms_data = validated_data.pop('programms', [])
        disciplines_data = validated_data.pop('disciplines', [])
        calendar_name = validated_data.pop('calendar')  # Добавлено новое поле

        # Извлекаем значение name из validated_data
        name = validated_data.pop("event_name")

        sport_type, _ = CalendarSport.objects.get_or_create(name=sport_type_name)
        sport_type_person_type, _ = CalendarSportType.objects.get_or_create(name=name)  # Используем извлеченное значение name
        calendar, _ = Calendar.objects.get_or_create(name=calendar_name)  # Создаем или получаем объект Calendar

        # Устанавливаем связь с объектом Calendar через поле calendar_sport
        sport_type.calendar = calendar
        sport_type.save()

        calendar_sport_info = CalendarSportInfo.objects.create(
            calendar_sport=sport_type,
            calendar_sport_type=sport_type_person_type,
            team=TeamInfo.objects.get_or_create(name=sport_type_person_type_name)[0],
            ekp=validated_data.get('ekp'),
            description=validated_data.get('description'),
            date_from=validated_data.get('date_from'),
            date_to=validated_data.get('date_to'),
            count=validated_data.get('count'),
            location=validated_data.get('location')
        )

        for gender_age in gender_age_data:
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
                raise serializers.ValidationError(gender_age_serializer.errors)

        for program_name in programms_data:
            program, _ = ProgramInfo.objects.get_or_create(name=program_name)
            ProgramFilter.objects.create(
                program=program,
                calendar_sport_info=calendar_sport_info
            )

        for discipline_name in disciplines_data:
            discipline, _ = DisciplineInfo.objects.get_or_create(name=discipline_name)
            DisciplineFilter.objects.create(
                discipline=discipline,
                calendar_sport_info=calendar_sport_info
            )

        return calendar_sport_info

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