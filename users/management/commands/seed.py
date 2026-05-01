import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


DEFAULT_PASSWORD = "password"
DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "seed_data.json"


class Command(BaseCommand):
    help = "Создаёт набор тестовых пользователей, навыков и проектов из JSON-файла."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            default=str(DEFAULT_DATA_PATH),
            help=(
                "Путь до JSON-файла с данными для загрузки. "
                "По умолчанию используется seed_data.json рядом с командой."
            ),
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующих тестовых пользователей и связанные проекты.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        data_path = Path(options["data"])
        if not data_path.is_file():
            raise CommandError(f"Файл с данными не найден: {data_path}")

        try:
            with data_path.open(encoding="utf-8") as fp:
                data = json.load(fp)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Не удалось разобрать JSON ({data_path}): {exc}") from exc

        skills_data = data.get("skills", [])
        users_data = data.get("users", [])
        projects_data = data.get("projects", [])

        if options["reset"]:
            emails = [u["email"] for u in users_data]
            deleted, _ = User.objects.filter(email__in=emails).delete()
            self.stdout.write(
                self.style.WARNING(f"Удалено объектов: {deleted}")
            )

        skills_by_name = {}
        for name in skills_data:
            skill, _ = Skill.objects.get_or_create(name=name)
            skills_by_name[name] = skill

        users_by_email = {}
        for item in users_data:
            user = User.objects.filter(email=item["email"]).first()
            if user is None:
                user = User.objects.create_user(
                    email=item["email"],
                    password=DEFAULT_PASSWORD,
                    name=item["name"],
                    surname=item["surname"],
                    about=item.get("about", ""),
                    phone=item.get("phone", ""),
                    github_url=item.get("github_url", ""),
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Создан пользователь {user.email}")
                )
            else:
                self.stdout.write(f"Пользователь {user.email} уже существует")
            users_by_email[user.email] = user

        for item in projects_data:
            owner = users_by_email[item["owner_email"]]
            project, created = Project.objects.get_or_create(
                owner=owner,
                name=item["name"],
                defaults={
                    "description": item.get("description", ""),
                    "github_url": item.get("github_url", ""),
                    "status": item.get("status", Project.STATUS_OPEN),
                },
            )
            project.skills.set(skills_by_name[s] for s in item.get("skills", []))
            participant_users = [
                users_by_email[email] for email in item.get("participants", [])
            ]
            project.participants.set([owner, *participant_users])
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Создан проект «{project.name}»")
                )
            else:
                self.stdout.write(f"Проект «{project.name}» уже существует")

        self.stdout.write(self.style.SUCCESS("Готово."))
