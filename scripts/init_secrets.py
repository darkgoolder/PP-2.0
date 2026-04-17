#!/usr/bin/env python
# scripts/init_secrets.py
"""Скрипт инициализации секретов в S3"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure import s3_storage, secret_repository
from app.config import settings


async def init_secrets():
    """Инициализация секретов"""
    print("=" * 60)
    print("🔐 Инициализация системы секретов S3")
    print("=" * 60)
    
    # Проверка подключения
    print("\n1. Проверка подключения к MinIO...")
    try:
        buckets = await s3_storage.list_objects(settings.secrets_bucket)
        print(f"   ✅ Подключено. Бакет: {settings.secrets_bucket}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    # Проверка существующих секретов
    print("\n2. Проверка существующих секретов...")
    keys = await secret_repository.list_secret_keys()
    if keys:
        print(f"   ✅ Найдено {len(keys)} секретов: {keys}")
    else:
        print("   ⚠️ Секреты не найдены")
        
        # Создание тестового секрета
        print("\n3. Создание тестового секрета...")
        await secret_repository.save_secret("INITIALIZED", "true")
        print("   ✅ Создан секрет: INITIALIZED")
    
    print("\n" + "=" * 60)
    print("🎉 Инициализация завершена!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(init_secrets())