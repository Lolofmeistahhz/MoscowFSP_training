import datetime

from django.db import models
from django.utils import timezone


class Calendar(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.CharField(max_length=255, verbose_name="Description")
    file = models.FileField(upload_to='static/files/calendars/', verbose_name="File", blank=True, null=True)

    class Meta:
        verbose_name = "Calendar"
        verbose_name_plural = "Calendars"

    def __str__(self):
        return self.name


class CalendarSport(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, verbose_name="Calendar", null=True)
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.CharField(max_length=255, verbose_name="Description", default="")
    image = models.ImageField(upload_to='static/img/sport/', verbose_name="Sport Image", blank=True, null=True)

    class Meta:
        verbose_name = "Calendar Sport"
        verbose_name_plural = "Calendar Sports"

    def __str__(self):
        return self.name


class CalendarSportType(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.CharField(max_length=255, verbose_name="Description")

    class Meta:
        verbose_name = "Calendar Sport Type"
        verbose_name_plural = "Calendar Sport Types"

    def __str__(self):
        return self.name


class SexCategory(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    sex = models.CharField(max_length=255, verbose_name="Sex")

    class Meta:
        verbose_name = "Sex Category"
        verbose_name_plural = "Sex Categories"

    def __str__(self):
        return self.sex


class AgeCategory(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    age = models.CharField(max_length=255, verbose_name="Age")

    class Meta:
        verbose_name = "Age Category"
        verbose_name_plural = "Age Categories"

    def __str__(self):
        return self.age


class CalendarSportInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    ekp = models.CharField(max_length=255, verbose_name="EKP")
    description = models.CharField(max_length=255, verbose_name="Description", default="")
    image = models.ImageField(upload_to='static/img/events/', verbose_name="Event Image", blank=True, null=True)
    calendar_sport_type = models.ForeignKey(CalendarSportType, on_delete=models.CASCADE,
                                            verbose_name="Calendar Sport Type")
    calendar_sport = models.ForeignKey(CalendarSport, on_delete=models.CASCADE, verbose_name="Calendar Sport",
                                       blank=True, null=True)
    team = models.ForeignKey('TeamInfo', on_delete=models.CASCADE, verbose_name="Team", default=None)
    date_from = models.DateField(verbose_name="Date From")
    date_to = models.DateField(verbose_name="Date To")
    location = models.CharField(max_length=255, verbose_name="Location")
    count = models.IntegerField(verbose_name="Count")
    perfomer = models.CharField(max_length=255, verbose_name="Perfomer")

    class Meta:
        verbose_name = "Calendar Sport Info"
        verbose_name_plural = "Calendar Sport Infos"
        ordering = ['-date_to', 'description']


    def __str__(self):
        return f"{self.calendar_sport} - {self.date_from}"


class TeamInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")

    class Meta:
        verbose_name = "Team Info"
        verbose_name_plural = "Team Infos"

    def __str__(self):
        return self.name


class Notifications(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")
    event_info = models.CharField(max_length=255, verbose_name="Event Info")
    calendar_sport_info = models.ForeignKey(CalendarSportInfo, on_delete=models.CASCADE, verbose_name="Calendar Sport",
                                            default=None)
    alert_datetime = models.DateTimeField(blank=True, verbose_name="Alert time", default=timezone.now())
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name="User")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return self.name


class ProgramInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")

    class Meta:
        verbose_name = "Program Info"
        verbose_name_plural = "Program Infos"

    def __str__(self):
        return self.name


class DisciplineInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")

    class Meta:
        verbose_name = "Discipline Info"
        verbose_name_plural = "Discipline Infos"

    def __str__(self):
        return self.name


class UserRole(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=255, verbose_name="Name")

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def __str__(self):
        return self.name


class User(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    user_role = models.ForeignKey(UserRole, on_delete=models.CASCADE, verbose_name="User Role", default=None)
    login = models.CharField(max_length=255, verbose_name="Login")
    password = models.CharField(max_length=255, verbose_name="Password")
    email = models.EmailField(verbose_name="Email")
    avatar = models.ImageField(upload_to='static/img/user/', verbose_name="Avatar", blank=True, null=True)
    tg_chat = models.CharField(max_length=255, verbose_name="TG ID", blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.login


class Files(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    file = models.FileField(upload_to='static/files/files/', verbose_name="File", blank=True, null=True)
    checksum = models.CharField(max_length=255, verbose_name="Checksum", default="")

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"

    def __str__(self):
        return self.file.name


class SexAgeFilter(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    age = models.ForeignKey(AgeCategory, on_delete=models.CASCADE, verbose_name="Age")
    sex = models.ForeignKey(SexCategory, on_delete=models.CASCADE, verbose_name="Sex")
    calendar_sport_info = models.ForeignKey(CalendarSportInfo, on_delete=models.CASCADE,
                                            verbose_name="Calendar Sport Info")

    class Meta:
        verbose_name = "Sex Age Filter"
        verbose_name_plural = "Sex Age Filters"

    def __str__(self):
        return f"{self.sex} - {self.age}"


class ProgramFilter(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    program = models.ForeignKey(ProgramInfo, on_delete=models.CASCADE, verbose_name="Program")
    calendar_sport_info = models.ForeignKey(CalendarSportInfo, on_delete=models.CASCADE,
                                            verbose_name="Calendar Sport Info")

    class Meta:
        verbose_name = "Program Filter"
        verbose_name_plural = "Program Filters"

    def __str__(self):
        return f"{self.program} - {self.calendar_sport_info}"


class DisciplineFilter(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    discipline = models.ForeignKey(DisciplineInfo, on_delete=models.CASCADE, verbose_name="Discipline")
    calendar_sport_info = models.ForeignKey(CalendarSportInfo, on_delete=models.CASCADE,
                                            verbose_name="Calendar Sport Info")

    class Meta:
        verbose_name = "Discipline Filter"
        verbose_name_plural = "Discipline Filters"

    def __str__(self):
        return f"{self.discipline} - {self.calendar_sport_info}"


class SavedFilters(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    name = models.CharField(max_length=255, verbose_name="Name")
    value = models.TextField(verbose_name="Value")

    class Meta:
        verbose_name = "Saved Filter"
        verbose_name_plural = "Saved Filters"

    def __str__(self):
        return f"{self.user.login} - {self.name}"
