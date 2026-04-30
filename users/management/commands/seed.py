from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


SKILLS = [
    "Python",
    "Django",
    "PostgreSQL",
    "Docker",
    "JavaScript",
    "React",
    "TypeScript",
    "HTML/CSS",
    "Figma",
    "Linux",
]


DEFAULT_PASSWORD = "password"


USERS = [
    {
        "email": "alice@example.com",
        "name": "Алиса",
        "surname": "Иванова",
        "about": "Backend-разработчик, увлекаюсь open source.",
        "phone": "+79990000001",
        "github_url": "https://github.com/alice",
        "skills": ["Python", "Django", "PostgreSQL"],
    },
    {
        "email": "bob@example.com",
        "name": "Борис",
        "surname": "Петров",
        "about": "Frontend-разработчик, ищу команду на pet-проект.",
        "phone": "+79990000002",
        "github_url": "https://github.com/bob",
        "skills": ["JavaScript", "React", "TypeScript"],
    },
    {
        "email": "carol@example.com",
        "name": "Каролина",
        "surname": "Сидорова",
        "about": "Дизайнер интерфейсов и немного фронта.",
        "phone": "+79990000003",
        "github_url": "https://github.com/carol",
        "skills": ["Figma", "HTML/CSS"],
    },
    {
        "email": "dan@example.com",
        "name": "Даниил",
        "surname": "Кузнецов",
        "about": "DevOps, Linux, инфраструктура.",
        "phone": "+79990000004",
        "github_url": "https://github.com/dan",
        "skills": ["Docker", "Linux", "PostgreSQL"],
    },
]


PROJECTS = [
    {
        "owner_email": "alice@example.com",
        "name": "Аналитический дашборд",
        "description": (
            "Сервис, агрегирующий данные из нескольких источников и "
            "показывающий метрики в реальном времени."
        ),
        "github_url": "https://github.com/alice/analytics",
        "status": Project.STATUS_OPEN,
        "skills": ["Python", "Django", "PostgreSQL"],
        "participants": ["bob@example.com"],
    },
    {
        "owner_email": "bob@example.com",
        "name": "Конструктор лендингов",
        "description": "Drag-and-drop редактор для быстрой сборки посадочных страниц.",
        "github_url": "https://github.com/bob/landing-builder",
        "status": Project.STATUS_OPEN,
        "skills": ["React", "TypeScript", "HTML/CSS"],
        "participants": ["carol@example.com"],
    },
    {
        "owner_email": "carol@example.com",
        "name": "Дизайн-система TeamFinder",
        "description": "Унифицированная библиотека UI-компонентов для проекта TeamFinder.",
        "github_url": "",
        "status": Project.STATUS_CLOSED,
        "skills": ["Figma", "HTML/CSS"],
        "participants": [],
    },
    {
        "owner_email": "dan@example.com",
        "name": "CI/CD для pet-проектов",
        "description": "Шаблоны GitHub Actions и Docker-образов для быстрого старта.",
        "github_url": "https://github.com/dan/cicd-templates",
        "status": Project.STATUS_OPEN,
        "skills": ["Docker", "Linux"],
        "participants": ["alice@example.com"],
    },
]


class Command(BaseCommand):
    help = "Создаёт набор тестовых пользователей, навыков и проектов для ревьюера."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующих тестовых пользователей и связанные проекты.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            emails = [u["email"] for u in USERS]
            deleted, _ = User.objects.filter(email__in=emails).delete()
            self.stdout.write(
                self.style.WARNING(f"Удалено объектов: {deleted}")
            )

        skills_by_name = {}
        for name in SKILLS:
            skill, _ = Skill.objects.get_or_create(name=name)
            skills_by_name[name] = skill

        users_by_email = {}
        for data in USERS:
            user = User.objects.filter(email=data["email"]).first()
            if user is None:
                user = User.objects.create_user(
                    email=data["email"],
                    password=DEFAULT_PASSWORD,
                    name=data["name"],
                    surname=data["surname"],
                    about=data["about"],
                    phone=data["phone"],
                    github_url=data["github_url"],
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Создан пользователь {user.email}")
                )
            else:
                self.stdout.write(f"Пользователь {user.email} уже существует")
            users_by_email[user.email] = user

        for data in PROJECTS:
            owner = users_by_email[data["owner_email"]]
            project, created = Project.objects.get_or_create(
                owner=owner,
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "github_url": data["github_url"],
                    "status": data["status"],
                },
            )
            project.skills.set(skills_by_name[s] for s in data["skills"])
            participant_users = [users_by_email[e] for e in data["participants"]]
            project.participants.set([owner, *participant_users])
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Создан проект «{project.name}»")
                )
            else:
                self.stdout.write(f"Проект «{project.name}» уже существует")

        self.stdout.write(self.style.SUCCESS("Готово."))
