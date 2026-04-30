from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "surname", "is_staff", "is_active")
    search_fields = ("email", "name", "surname")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)
