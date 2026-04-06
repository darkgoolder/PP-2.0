# Многостадийная сборка для оптимизации
FROM python:3.9-slim AS builder

WORKDIR /app

# Установка системных зависимостей (минимально необходимые)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Копируем только requirements.txt (не pyproject.toml и uv.lock)
COPY requirements.txt ./

# Устанавливаем только необходимые пакеты (без кэша и с оптимизациями)
RUN uv pip install --system --no-cache --no-deps -r requirements.txt || \
    uv pip install --system --no-cache -r requirements.txt

# Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Установка минимальных системных зависимостей для работы
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем только необходимые части из builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY app/ ./app/
COPY app/static/ ./app/static/

# Создаем необходимые директории
RUN mkdir -p models uploads

# Очищаем кэш pip
RUN rm -rf /root/.cache/pip

# Переменные окружения
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Открываем порт
EXPOSE 8000

# Здоровье проверка
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]