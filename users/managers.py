"""Менеджеры моделей приложения users."""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("У пользователя должен быть указан email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        from users.avatar import build_letter_avatar

        content = build_letter_avatar(user.name or "?")
        user.avatar.save(content.name, content, save=False)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        if "name" not in extra_fields:
            extra_fields["name"] = "Admin"
        if "surname" not in extra_fields:
            extra_fields["surname"] = "User"

        return self.create_user(email, password, **extra_fields)
