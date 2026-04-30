from django import template

register = template.Library()


@register.filter(name="ru_plural")
def ru_plural(count, forms="участник,участника,участников"):
    """Возвращает правильную форму существительного для числа.

    Использование в шаблоне:
        {{ count }} {{ count|ru_plural:"участник,участника,участников" }}
    """
    try:
        n = abs(int(count))
    except (TypeError, ValueError):
        return ""

    parts = [p.strip() for p in forms.split(",")]
    if len(parts) != 3:
        return ""

    one, few, many = parts
    if n % 100 in (11, 12, 13, 14):
        return many
    last = n % 10
    if last == 1:
        return one
    if last in (2, 3, 4):
        return few
    return many
