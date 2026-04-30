import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

GITHUB_HOST = "github.com"


def github_url_validator(value: str):
    if not value:
        return
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if GITHUB_HOST not in host:
        raise ValidationError("Ссылка должна вести на GitHub.", code="invalid_github")


def normalize_phone_digits(value: str) -> str:
    """Приводит номер к формату +7XXXXXXXXXX для хранения и сравнения уникальности."""
    v = value.strip()
    if v.startswith("+7") and len(v) == 12:
        return v
    if v.startswith("8") and len(v) == 11:
        return "+7" + v[1:]
    return v
