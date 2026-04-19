#!/usr/bin/env python
# scripts/add_secrets.py
"""Скрипт для добавления секретов в MinIO S3"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure import secret_repository
from app.config import settings


async def add_secrets():
    """Добавление секретов в хранилище"""
    print("=" * 60)
    print("🔐 Добавление секретов в MinIO S3")
    print("=" * 60)
    
    # Список секретов для добавления
    secrets_to_add = {
        # JWT секреты
        "JWT_SECRET_KEY": "your-super-secret-jwt-key-change-me",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7",
        
        # База данных
        "DB_PASSWORD": "secure_db_password_123",
        "DB_USER": "wagon_user",
        "DB_NAME": "wagon_db",
        
        # MinIO (если нужно хранить)
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin123",
        
        # API ключи
        "API_KEY": "wagon_api_key_2024",
        "API_SECRET": "wagon_api_secret_2024",
        
        # Админ токен
        "ADMIN_API_TOKEN": "admin_token_for_wagon_api",
        
        # Redis (если используется)
        "REDIS_PASSWORD": "redis_secure_password",
        
        # Внешние сервисы
        "SENTRY_DSN": "https://example@sentry.io/123456",
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxx/yyy/zzz",
        
        # SMTP для email
        "SMTP_PASSWORD": "smtp_secure_password",
        "SMTP_USER": "noreply@wagon-classification.com",
        
        # Модель ML
        "MODEL_API_KEY": "ml_model_api_key",
        "MODEL_API_URL": "https://api.model-service.com/v1/predict",
    }
    
    print("\n📝 Добавляемые секреты:")
    for key in secrets_to_add.keys():
        print(f"   • {key}")
    
    print("\n💾 Сохранение секретов в S3...")
    
    for key, value in secrets_to_add.items():
        try:
            await secret_repository.save_secret(key, value, encrypt=True)
            print(f"   ✅ {key} - сохранён")
        except Exception as e:
            print(f"   ❌ {key} - ошибка: {e}")
    
    # Проверка что секреты сохранились
    print("\n🔍 Проверка сохранённых секретов...")
    keys = await secret_repository.list_secret_keys()
    print(f"   ✅ Всего секретов в хранилище: {len(keys)}")
    
    for key in keys:
        print(f"      • {key}")
    
    print("\n" + "=" * 60)
    print("🎉 Секреты успешно добавлены в MinIO S3!")
    print("=" * 60)
    
    # Информация о доступе
    print("\n📌 Доступ к секретам через API:")
    print(f"   • Получить секрет: GET /{settings.api_v1_prefix}/secrets/get/{{key}}")
    print(f"   • Список секретов: GET /{settings.api_v1_prefix}/secrets/list")
    print(f"   • Health check: GET /{settings.api_v1_prefix}/secrets/health")


if __name__ == "__main__":
    asyncio.run(add_secrets())