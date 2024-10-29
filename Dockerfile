# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.4
FROM python:${PYTHON_VERSION}-slim as base

# Предотвращает создание pyc файлов
ENV PYTHONDONTWRITEBYTECODE=1

# Отключает буферизацию вывода
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Создание не-привилегированного пользователя
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Создание директории logs и установка прав
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

# Загрузка зависимостей
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Переключение на пользователя appuser
USER appuser

# Копирование исходного кода
COPY . .

# Экспонирование порта приложения
EXPOSE 8000

# Запуск приложения
CMD ["python", "main.py"]
