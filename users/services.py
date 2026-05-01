"""Вспомогательные функции уровня приложения users."""

from django.core.paginator import Paginator


def paginate_queryset(request, queryset, per_page):
    """Создаёт страницу пагинации по queryset с учётом GET-параметра ?page=."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))
