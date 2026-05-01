"""Переиспользуемые миксины для форм."""

from projects.validators import github_url_validator


class GithubUrlCleanMixin:
    """Нормализует и валидирует поле github_url у любой формы, где оно есть."""

    def clean_github_url(self):
        value = (self.cleaned_data.get("github_url") or "").strip()
        if value:
            github_url_validator(value)
        return value
