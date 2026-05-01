from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from projects.models import Project, Skill
from users.models import User


class ProjectListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="author@example.com",
            password="password",
            name="Автор",
            surname="Авторов",
        )
        cls.project = Project.objects.create(
            name="Тестовый проект",
            description="Описание",
            owner=cls.user,
            status=Project.STATUS_OPEN,
        )

    def test_list_page_renders(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.project.name)

    def test_detail_page_renders(self):
        response = self.client.get(
            reverse("projects:detail", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.project.name)

    def test_root_redirects_to_project_list(self):
        response = self.client.get(reverse("root"))
        self.assertRedirects(response, reverse("projects:list"))

    def test_anonymous_cannot_create_project(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), response.url)


class ProjectActionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Владелец",
            surname="Проекта",
        )
        cls.other = User.objects.create_user(
            email="other@example.com",
            password="password",
            name="Другой",
            surname="Юзер",
        )
        cls.project = Project.objects.create(
            name="P",
            owner=cls.owner,
            status=Project.STATUS_OPEN,
        )

        cls.owner_client = Client()
        cls.owner_client.force_login(cls.owner)

        cls.other_client = Client()
        cls.other_client.force_login(cls.other)

    def test_owner_can_complete_project(self):
        response = self.owner_client.post(
            reverse("projects:complete", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    def test_other_user_cannot_complete_project(self):
        response = self.other_client.post(
            reverse("projects:complete", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_user_can_join_and_leave_project(self):
        url = reverse(
            "projects:toggle_participate", kwargs={"pk": self.project.pk}
        )
        response = self.other_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(self.project.participants.filter(pk=self.other.pk).exists())

        response = self.other_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(self.project.participants.filter(pk=self.other.pk).exists())


class SkillFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="o@example.com",
            password="password",
            name="O",
            surname="O",
        )
        cls.python = Skill.objects.create(name="Python")
        cls.django = Skill.objects.create(name="Django")
        cls.python_project = Project.objects.create(
            name="Python project", owner=cls.owner, status=Project.STATUS_OPEN
        )
        cls.python_project.skills.add(cls.python)
        cls.django_project = Project.objects.create(
            name="Django project", owner=cls.owner, status=Project.STATUS_OPEN
        )
        cls.django_project.skills.add(cls.django)

    def test_filter_by_skill_keeps_matching_projects(self):
        response = self.client.get(reverse("projects:list"), {"skill": "Python"})
        self.assertContains(response, "Python project")
        self.assertNotContains(response, "Django project")

    def test_skill_autocomplete_returns_matches(self):
        response = self.client.get(reverse("projects:skills_autocomplete"), {"q": "Py"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        names = [item["name"] for item in data]
        self.assertIn("Python", names)
