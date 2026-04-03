# Используем Python 3.9-slim (Debian Bookworm - более стабильная версия)
FROM python:3.9-slim

# Создаем пользователя с UID 1000 (требование HF Spaces)
RUN useradd -m -u 1000 user

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Переключаемся на пользователя
USER user

# Устанавливаем домашнюю директорию
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Устанавливаем рабочую директорию
WORKDIR $HOME/app

# Копируем зависимости
COPY --chown=user requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY --chown=user . .

# Создаем необходимые папки
RUN mkdir -p models uploads

# Устанавливаем переменные окружения
ENV MODEL_PATH=/home/user/app/models/best_model.pth \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Открываем порт (HF Spaces требует 7860)
EXPOSE 7860

# Healthcheck для HF Spaces
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Запускаем приложение на порту 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]