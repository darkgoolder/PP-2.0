# Многостадийная сборка для оптимизации
FROM python:3.9-slim AS builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Копируем зависимости
COPY pyproject.toml uv.lock requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Копируем зависимости из builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY app/ ./app/
COPY models/ ./models/
COPY uploads/ ./uploads/

# Копируем статические файлы
COPY app/static/ ./app/static/

# Переменные окружения
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Открываем порт
EXPOSE 8000

# Здоровье проверка
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]