from django import forms

from projects.form_mixins import GithubUrlCleanMixin

from .models import Project


class ProjectForm(GithubUrlCleanMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на репозиторий GitHub",
            "status": "Статус проекта",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Название проекта",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Описание проекта",
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "placeholder": "https://github.com/логин/название-репозитория",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = Project.STATUS_CHOICES
