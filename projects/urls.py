from django.urls import path

from projects import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("create-project/", views.ProjectCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path("<int:pk>/complete/", views.complete_project, name="complete"),
    path(
        "<int:pk>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path("skills/", views.skills_autocomplete, name="skills_autocomplete"),
    path("<int:pk>/skills/add/", views.ProjectSkillAddView.as_view(), name="skill_add"),
    path(
        "<int:pk>/skills/<int:skill_id>/remove/",
        views.ProjectSkillRemoveView.as_view(),
        name="skill_remove",
    ),
]
