#!/usr/bin/env python
# scripts/init_secrets_s3.py
"""
Скрипт инициализации секретов в S3
Запуск: python scripts/init_secrets_s3.py
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("🔐 Инициализация системы секретов S3")
print("=" * 60)
print("")

# Шаг 1: Импорт модулей
print("1. Загрузка модулей...")
try:
    from services.s3_secrets import secrets_manager, env_secrets
    from services.s3_client import s3_client
    from config.settings import settings
    print("   ✅ Модули загружены")
except Exception as e:
    print(f"   ❌ Ошибка загрузки модулей: {e}")
    sys.exit(1)

# Шаг 2: Проверка подключения к MinIO
print("\n2. Проверка подключения к MinIO...")
try:
    buckets = s3_client.client.list_buckets()
    print(f"   ✅ Подключение успешно. Найдено {len(buckets)} бакетов")
except Exception as e:
    print(f"   ❌ Ошибка подключения: {e}")
    print("\n   Убедитесь что MinIO запущен командой:")
    print('   docker run -d --name wagon-minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin123" -v minio_data:/data minio/minio server /data --console-address ":9001"')
    sys.exit(1)

# Шаг 3: Инициализация бакетов
print("\n3. Инициализация S3 бакетов...")
buckets_to_create = [
    settings.secrets_bucket,
    settings.s3_bucket_images,
    settings.s3_bucket_models,
    settings.s3_bucket_backups
]

for bucket in buckets_to_create:
    try:
        if not s3_client.client.bucket_exists(bucket):
            s3_client.client.make_bucket(bucket)
            print(f"   ✅ Создан бакет: {bucket}")
        else:
            print(f"   ✅ Бакет существует: {bucket}")
    except Exception as e:
        print(f"   ❌ Ошибка с бакетом {bucket}: {e}")

# Шаг 4: Инициализация секретов
print("\n4. Инициализация секретов...")

required_secrets = {
    "SECRET_KEY": settings.secret_key.get_secret_value(),
    "DB_PASSWORD": settings.db_password.get_secret_value(),
    "MINIO_SECRET_KEY": settings.minio_secret_key.get_secret_value(),
}

# Сохраняем секреты
try:
    secrets_manager.save_secrets_to_s3(required_secrets, encrypt=True)
    print(f"   ✅ Сохранено {len(required_secrets)} секретов в S3")
    for key in required_secrets.keys():
        print(f"      • {key}")
except Exception as e:
    print(f"   ❌ Ошибка сохранения секретов: {e}")

# Шаг 5: Тест загрузки секретов
print("\n5. Тест загрузки секретов...")
try:
    loaded = secrets_manager.load_secrets_from_s3(decrypt=True)
    if loaded:
        print(f"   ✅ Загружено {len(loaded)} секретов:")
        for key in loaded.keys():
            print(f"      • {key}")
    else:
        print("   ⚠️ Не удалось загрузить секреты")
except Exception as e:
    print(f"   ❌ Ошибка загрузки: {e}")

# Шаг 6: Создание бэкапа
print("\n6. Создание бэкапа...")
try:
    import json
    from datetime import datetime
    backup_name = f"secrets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = secrets_manager.load_secrets_from_s3(decrypt=False)
    if data:
        s3_client.client.put_object(
            bucket_name=settings.s3_bucket_backups,
            object_name=f"secrets/{backup_name}",
            data=json.dumps(data, indent=2).encode(),
            length=len(json.dumps(data))
        )
        print(f"   ✅ Создан бэкап: {backup_name}")
    else:
        print("   ⚠️ Нет данных для бэкапа")
except Exception as e:
    print(f"   ❌ Ошибка создания бэкапа: {e}")

print("\n" + "=" * 60)
print("🎉 Инициализация завершена!")
print("=" * 60)
print("\n📌 Доступ к веб-консоли MinIO:")
print("   http://localhost:9001")
print("   Login: minioadmin")
print("   Password: minioadmin123")