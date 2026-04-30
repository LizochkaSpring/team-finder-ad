import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from projects.validators import github_url_validator, normalize_phone_digits

User = get_user_model()

PHONE_PATTERN = re.compile(r"^(?:\+7|8)\d{10}$")


class RegisterForm(forms.Form):
    name = forms.CharField(label="Имя", max_length=124)
    surname = forms.CharField(label="Фамилия", max_length=124)
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self):
        email = self.cleaned_data["email"].strip().lower()
        return User.objects.create_user(
            email=email,
            password=self.cleaned_data["password"],
            name=self.cleaned_data["name"],
            surname=self.cleaned_data["surname"],
        )


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return ""
        if not PHONE_PATTERN.match(raw):
            raise forms.ValidationError(
                "Допустимые форматы: 8XXXXXXXXXX или +7XXXXXXXXXX."
            )
        normalized = normalize_phone_digits(raw)
        taken = (
            User.objects.exclude(pk=self.instance.pk)
            .exclude(phone="")
            .filter(phone=normalized)
            .exists()
        )
        if taken:
            raise forms.ValidationError("Этот номер уже занят другим пользователем.")
        return normalized

    def clean_github_url(self):
        value = (self.cleaned_data.get("github_url") or "").strip()
        if value:
            github_url_validator(value)
        return value


class UserPasswordChangeForm(PasswordChangeForm):
    pass
