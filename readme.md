# TeamFinder

Pet-проект на Django + PostgreSQL. Реализован **Вариант №3**: навыки у проектов
и фильтр проектов по навыкам.

## Запуск через Docker (рекомендуется)

```bash
cp .env_example .env          # Windows: copy .env_example .env
docker compose up --build
```

Контейнер `web` сам выполнит `migrate`, `seed`, `collectstatic` и поднимет
сервер. Открыть <http://localhost:8000/>.

## Запуск локально

Требуется Python 3.11+, Docker (только для БД).

```bash
python -m venv venv
# Windows
venv\Scripts\Activate.ps1
# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt
cp .env_example .env

docker compose up -d db
python manage.py migrate
python manage.py seed
python manage.py runserver
```

## Тестовые учётные записи

Создаются командой `python manage.py seed`. Пароль у всех — **`password`**.

| Email                | Имя               |
|----------------------|-------------------|
| `alice@example.com`  | Алиса Иванова     |
| `bob@example.com`    | Борис Петров      |
| `carol@example.com`  | Каролина Сидорова |
| `dan@example.com`    | Даниил Кузнецов   |

Пересоздать тестовые данные: `python manage.py seed --reset`.

Создать суперпользователя для админки: `python manage.py createsuperuser`.
