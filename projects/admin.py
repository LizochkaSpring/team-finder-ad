from django.contrib import admin

from projects.models import Project, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "skills_list", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")
    filter_horizontal = ("participants", "skills")

    @admin.display(description="Навыки")
    def skills_list(self, obj):
        return ", ".join(obj.skills.values_list("name", flat=True))
