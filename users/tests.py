from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from users.models import User


class UserAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_user = User.objects.create_user(
            email="login@example.com",
            password="password",
            name="Логин",
            surname="Логиныч",
        )

    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            data={
                "name": "Тест",
                "surname": "Тестов",
                "email": "test@example.com",
                "password": "password",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_login_with_valid_credentials_redirects_to_projects(self):
        response = self.client.post(
            reverse("users:login"),
            data={"email": "login@example.com", "password": "password"},
        )
        self.assertRedirects(response, reverse("projects:list"))

    def test_login_with_invalid_credentials_shows_error(self):
        response = self.client.post(
            reverse("users:login"),
            data={"email": "noone@example.com", "password": "x"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Неверный")

    def test_participants_page_is_public(self):
        response = self.client.get(reverse("users:participants"))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class UserProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Хозяин",
            surname="Профиля",
        )

    def test_anonymous_can_view_profile(self):
        response = self.client.get(
            reverse("users:detail", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_cannot_edit_profile(self):
        response = self.client.get(reverse("users:edit_profile"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), response.url)
