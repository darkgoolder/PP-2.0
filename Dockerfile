# # Многостадийная сборка для оптимизации
# FROM python:3.9-slim AS builder

# WORKDIR /app

# # Установка системных зависимостей
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# # Установка uv
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# # Копируем requirements.txt
# COPY requirements.txt ./

# # Устанавливаем все зависимости
# RUN uv pip install --system --no-cache -r requirements.txt

# # Финальный образ
# FROM python:3.9-slim

# WORKDIR /app

# # Установка минимальных системных зависимостей
# RUN apt-get update && apt-get install -y \
#     libgl1 \
#     libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# # Копируем установленные пакеты из builder
# COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
# COPY --from=builder /usr/local/bin /usr/local/bin

# # Копируем код приложения (включает presentation/static)
# COPY app/ ./app/

# # Создаем необходимые директории
# RUN mkdir -p models uploads

# # Переменные окружения
# ENV PYTHONPATH=/app
# ENV ENVIRONMENT=production

# # Открываем порт
# EXPOSE 8000

# # Здоровье проверка
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# # Запуск приложения
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Многостадийная сборка для оптимизации
FROM python:3.9-slim AS builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Копируем requirements.txt
COPY requirements.txt ./

# Устанавливаем все зависимости
RUN uv pip install --system --no-cache -r requirements.txt

# ТОЛЬКО ОЧИСТКА (безопасно)
RUN find /usr/local/lib/python3.9/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.9/site-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /root/.cache/pip

# Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Установка минимальных системных зависимостей
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY app/ ./app/

# Создаем необходимые директории
RUN mkdir -p models uploads

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]