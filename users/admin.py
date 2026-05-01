from django.contrib import admin
from django.utils.html import format_html

from users.models import User


AVATAR_THUMBNAIL_SIZE_PX = 40


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "avatar_thumbnail",
        "email",
        "name",
        "surname",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "name", "surname")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)

    @admin.display(description="Аватар")
    def avatar_thumbnail(self, obj):
        if not obj.avatar:
            return ""
        return format_html(
            '<img src="{}" width="{}" height="{}" style="border-radius:50%;object-fit:cover;" />',
            obj.avatar.url,
            AVATAR_THUMBNAIL_SIZE_PX,
            AVATAR_THUMBNAIL_SIZE_PX,
        )
