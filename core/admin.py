from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Test, UserAccount, UserRole

@admin.register(Test)
class TestAdmin(ModelAdmin):
    list_display = ('name', 'age')
    search_fields = ('name',)

@admin.register(UserRole)
class UserRoleAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserAccount)
class UserAccountAdmin(ModelAdmin):
    list_display = ('login', 'id_role')
    search_fields = ('login',)
    list_filter = ('id_role',)