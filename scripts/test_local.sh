#!/bin/bash
# Скрипт для локального тестирования CI/CD пайплайна

echo "🔍 Running local CI/CD simulation..."

# 1. Линтинг
echo "📝 Running linters..."
ruff check .
black --check .

# 2. Тесты
echo "🧪 Running tests..."
pytest tests/ -v --cov=app

# 3. Сборка Docker
echo "🐳 Building Docker image..."
docker build -t wagon-api-test .

# 4. Запуск контейнера
echo "🚀 Starting container..."
docker run -d -p 8001:8000 --name wagon-api-test wagon-api-test

# 5. Проверка здоровья
echo "🏥 Checking health..."
sleep 5
curl http://localhost:8001/api/v1/health

# 6. Очистка
echo "🧹 Cleaning up..."
docker stop wagon-api-test
docker rm wagon-api-test

echo "✅ Local CI/CD simulation complete!"