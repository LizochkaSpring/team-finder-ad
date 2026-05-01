"""Переиспользуемые миксины для view-классов приложения projects."""

from django.contrib.auth.mixins import UserPassesTestMixin


class OwnerOrStaffMixin(UserPassesTestMixin):
    """Доступ разрешён владельцу объекта (через `get_object`) или сотруднику."""

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff or obj.owner_id == self.request.user.id
