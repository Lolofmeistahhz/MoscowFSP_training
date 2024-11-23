from django.contrib import admin
from django_celery_beat.admin import TaskSelectWidget, PeriodicTaskForm
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule
from unfold.admin import ModelAdmin
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget

from .models import (
    Calendar, CalendarSport, CalendarSportType, SexCategory, AgeCategory,
    CalendarSportInfo, TeamInfo, Notifications, ProgramInfo, DisciplineInfo,
    UserRole, User, Files, SexAgeFilter, ProgramFilter, DisciplineFilter,
    SavedFilters
)

from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

from django_celery_beat.admin import ClockedScheduleAdmin as BaseClockedScheduleAdmin
from django_celery_beat.admin import CrontabScheduleAdmin as BaseCrontabScheduleAdmin
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
from django_celery_beat.admin import PeriodicTaskForm, TaskSelectWidget

admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


@admin.register(Calendar)
class CalendarAdmin(ModelAdmin):
    list_display = ('id', 'name', 'description', 'file')
    search_fields = ('name', 'description')


@admin.register(CalendarSport)
class CalendarSportAdmin(ModelAdmin):
    list_display = ('id', 'calendar', 'name', 'description', 'image')
    search_fields = ('name', 'description')


@admin.register(CalendarSportType)
class CalendarSportTypeAdmin(ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name', 'description')


@admin.register(SexCategory)
class SexCategoryAdmin(ModelAdmin):
    list_display = ('id', 'sex')
    search_fields = ('sex',)


@admin.register(AgeCategory)
class AgeCategoryAdmin(ModelAdmin):
    list_display = ('id', 'age')
    search_fields = ('age',)


@admin.register(CalendarSportInfo)
class CalendarSportInfoAdmin(ModelAdmin):
    list_display = ('id', 'calendar_sport', 'date_from', 'date_to', 'location', 'image')
    search_fields = ('calendar_sport__name', 'location')


@admin.register(TeamInfo)
class TeamInfoAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Notifications)
class NotificationsAdmin(ModelAdmin):
    list_display = ('id', 'name', 'event_info', 'calendar_sport', 'user')
    search_fields = ('name', 'event_info')


@admin.register(ProgramInfo)
class ProgramInfoAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(DisciplineInfo)
class DisciplineInfoAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(UserRole)
class UserRoleAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'user_role', 'login', 'email', 'avatar', 'tg_chat')
    search_fields = ('login', 'email')


@admin.register(Files)
class FilesAdmin(ModelAdmin):
    list_display = ('id', 'file', 'checksum')
    search_fields = ('checksum',)


@admin.register(SexAgeFilter)
class SexAgeFilterAdmin(ModelAdmin):
    list_display = ('id', 'age', 'sex', 'calendar_sport_info')
    search_fields = ('age__age', 'sex__sex')


@admin.register(ProgramFilter)
class ProgramFilterAdmin(ModelAdmin):
    list_display = ('id', 'program', 'calendar_sport_info')
    search_fields = ('program__name', 'calendar_sport_info__calendar_sport__name')


@admin.register(DisciplineFilter)
class DisciplineFilterAdmin(ModelAdmin):
    list_display = ('id', 'discipline', 'calendar_sport_info')
    search_fields = ('discipline__name', 'calendar_sport_info__calendar_sport__name')


@admin.register(SavedFilters)
class SavedFiltersAdmin(ModelAdmin):
    list_display = ('id', 'user', 'name', 'value')
    search_fields = ('user__login', 'name')


class UnfoldTaskSelectWidget(UnfoldAdminSelectWidget, TaskSelectWidget): pass


class UnfoldPeriodicTaskForm(PeriodicTaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].widget = UnfoldAdminTextInputWidget()
        self.fields["regtask"].widget = UnfoldTaskSelectWidget()


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(BasePeriodicTaskAdmin, ModelAdmin):
    form = UnfoldPeriodicTaskForm
    ordering = ('-enabled',)


@admin.register(IntervalSchedule)
class IntervalScheduleAdmin(ModelAdmin): pass


@admin.register(CrontabSchedule)
class CrontabScheduleAdmin(BaseCrontabScheduleAdmin, ModelAdmin): pass


@admin.register(SolarSchedule)
class SolarScheduleAdmin(ModelAdmin): pass


@admin.register(ClockedSchedule)
class ClockedScheduleAdmin(BaseClockedScheduleAdmin, ModelAdmin): pass
