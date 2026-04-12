# test_config.py
"""
Простой тест для проверки config.py
Запуск: python test_config.py
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь Python
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("\n" + "="*60)
print("🧪 ТЕСТИРОВАНИЕ CONFIG.PY")
print("="*60)

# 1. Проверяем импорт
print("\n1. ПРОВЕРКА ИМПОРТА...")
try:
    from config import settings, get_settings
    print("   ✅ Импорт settings успешен")
except ImportError as e:
    print(f"   ❌ Ошибка импорта: {e}")
    print("   Проверьте что в config.py есть переменная 'settings'")
    sys.exit(1)

# 2. Проверяем базовые атрибуты
print("\n2. ПРОВЕРКА АТРИБУТОВ...")
try:
    print(f"   • APP_ENV: {settings.app_env}")
    print(f"   • DEBUG: {settings.debug}")
    print(f"   • API_PREFIX: {settings.api_prefix}")
    print(f"   • API_TITLE: {settings.api_title}")
    print("   ✅ Атрибуты доступны")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

# 3. Проверяем свойства
print("\n3. ПРОВЕРКА СВОЙСТВ (PROPERTIES)...")
try:
    print(f"   • CLASS_NAMES_LIST: {settings.class_names_list}")
    print(f"   • NUM_CLASSES: {settings.num_classes}")
    print(f"   • DEVICE: {settings.device}")
    print(f"   • IS_DEVELOPMENT: {settings.is_development}")
    print("   ✅ Свойства работают")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

# 4. Проверяем методы
print("\n4. ПРОВЕРКА МЕТОДОВ...")
try:
    # Проверка расширения файла
    result = settings.validate_file_extension("test.jpg")
    print(f"   • validate_file_extension('test.jpg'): {result}")
    
    # Проверка получения индекса класса
    idx = settings.get_class_index("pered")
    print(f"   • get_class_index('pered'): {idx}")
    
    print("   ✅ Методы работают")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 5. Проверка путей
print("\n5. ПРОВЕРКА ПУТЕЙ...")
try:
    print(f"   • MODEL_PATH: {settings.model_path}")
    print(f"   • Файл существует: {settings.model_path.exists()}")
    print("   ✅ Пути корректны")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 6. Проверка настроек базы данных
print("\n6. ПРОВЕРКА НАСТРОЕК БД...")
try:
    db_type = settings.database_url.split("://")[0] if "://" in settings.database_url else "unknown"
    print(f"   • Тип БД: {db_type}")
    print(f"   • DB_POOL_SIZE: {settings.db_pool_size}")
    print("   ✅ Настройки БД корректны")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 7. Проверка безопасности
print("\n7. ПРОВЕРКА БЕЗОПАСНОСТИ...")
try:
    print(f"   • ALGORITHM: {settings.algorithm}")
    print(f"   • ACCESS_TOKEN_EXPIRE_MINUTES: {settings.access_token_expire_minutes}")
    has_secret = len(settings.secret_key.get_secret_value()) > 0
    print(f"   • SECRET_KEY установлен: {has_secret}")
    print("   ✅ Настройки безопасности корректны")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 8. Проверка model_dump
print("\n8. ПРОВЕРКА model_dump()...")
try:
    config_dict = settings.model_dump()
    print(f"   • Ключей в конфиге: {len(config_dict)}")
    print(f"   • app_env: {config_dict.get('app_env')}")
    print("   ✅ model_dump() работает")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "="*60)
print("🎉 ТЕСТЫ ЗАВЕРШЕНЫ!")
print("="*60)

# Проверка get_settings функции
print("\n📌 Дополнительно:")
try:
    settings2 = get_settings()
    print(f"   ✅ get_settings() работает, вернула тот же объект: {settings2 is settings}")
except Exception as e:
    print(f"   ❌ get_settings() ошибка: {e}")