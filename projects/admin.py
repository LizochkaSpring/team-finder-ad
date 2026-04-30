from django.contrib import admin

from projects.models import Project, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")
    filter_horizontal = ("participants", "skills")


admin.site.register(Project, ProjectAdmin)
