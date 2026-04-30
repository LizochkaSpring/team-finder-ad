from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/")
    phone = models.CharField(max_length=12, blank=True)
    github_url = models.URLField(blank=True)
    about = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.name} {self.surname}".strip()

    def get_short_name(self):
        return self.name


@receiver(pre_save, sender=User)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    """Удаляет файл предыдущего аватара при загрузке нового."""
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    old_avatar = old.avatar
    new_avatar = instance.avatar
    if old_avatar and old_avatar != new_avatar:
        old_avatar.delete(save=False)


@receiver(post_delete, sender=User)
def delete_avatar_on_user_delete(sender, instance, **kwargs):
    if instance.avatar:
        instance.avatar.delete(save=False)
