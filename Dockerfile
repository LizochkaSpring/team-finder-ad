FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY --chown=app:app requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY --chown=app:app . .

RUN mkdir -p /app/media /app/staticfiles && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
