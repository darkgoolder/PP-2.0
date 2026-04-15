# services/s3_secrets.py
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import logging

from config.settings import settings, secrets_loader
from services.s3_client import s3_client

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Менеджер для безопасного хранения и управления секретами в S3
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Получение или создание ключа шифрования"""
        key_path = Path.home() / ".wagon_encryption_key"
        
        if key_path.exists():
            with open(key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
            # Устанавливаем права только для владельца
            key_path.chmod(0o600)
            logger.info(f"✅ Создан новый ключ шифрования: {key_path}")
            return key
    
    def encrypt_secret(self, secret: str) -> str:
        """Шифрование секрета"""
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted: str) -> str:
        """Дешифрование секрета"""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def save_secrets_to_s3(self, secrets: Dict[str, str], encrypt: bool = True):
        """
        Сохранение секретов в S3 с шифрованием
        
        Args:
            secrets: Словарь с секретами
            encrypt: Шифровать ли секреты
        """
        # Шифруем секреты
        if encrypt:
            secrets = {k: self.encrypt_secret(v) for k, v in secrets.items()}
        
        # Добавляем метаданные
        data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "environment": settings.app_env,
            "secrets": secrets
        }
        
        # Сохраняем в S3
        secrets_loader.save_secrets_to_s3(data)
        logger.info("✅ Секреты сохранены в S3")
    
    def load_secrets_from_s3(self, decrypt: bool = True) -> Dict[str, str]:
        """
        Загрузка секретов из S3
        
        Args:
            decrypt: Дешифровать ли секреты
        
        Returns:
            Словарь с секретами
        """
        data = secrets_loader.load_secrets_from_s3()
        
        if not data:
            return {}
        
        secrets_dict = data.get("secrets", {})
        
        # Дешифруем секреты
        if decrypt:
            secrets_dict = {k: self.decrypt_secret(v) for k, v in secrets_dict.items()}
        
        return secrets_dict
    
    def backup_secrets(self, backup_name: Optional[str] = None):
        """Создание бэкапа секретов"""
        if backup_name is None:
            backup_name = f"secrets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        secrets = self.load_secrets_from_s3(decrypt=False)
        
        # Сохраняем бэкап в отдельный бакет
        s3_client.client.put_object(
            bucket_name=settings.s3_bucket_backups,
            object_name=f"secrets/{backup_name}",
            data=json.dumps(secrets, indent=2).encode(),
            length=len(json.dumps(secrets))
        )
        
        logger.info(f"✅ Бэкап секретов создан: {backup_name}")
        return backup_name
    
    def restore_secrets(self, backup_name: str):
        """Восстановление секретов из бэкапа"""
        try:
            response = s3_client.client.get_object(
                bucket_name=settings.s3_bucket_backups,
                object_name=f"secrets/{backup_name}"
            )
            secrets = json.loads(response.read())
            
            self.save_secrets_to_s3(secrets, encrypt=False)
            logger.info(f"✅ Секреты восстановлены из бэкапа: {backup_name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            raise
    
    def list_backups(self) -> list:
        """Список доступных бэкапов секретов"""
        try:
            objects = s3_client.client.list_objects(
                bucket_name=settings.s3_bucket_backups,
                prefix="secrets/"
            )
            return [obj.object_name.replace("secrets/", "") for obj in objects]
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка бэкапов: {e}")
            return []
    
    def rotate_secret(self, secret_name: str, new_value: str):
        """Ротация конкретного секрета"""
        data = secrets_loader.load_secrets_from_s3()
        
        if not data:
            data = {"version": "1.0", "secrets": {}}
        
        secrets_dict = data.get("secrets", {})
        
        if secret_name in secrets_dict:
            secrets_dict[secret_name] = self.encrypt_secret(new_value)
            data["secrets"] = secrets_dict
            data["updated_at"] = datetime.now().isoformat()
            
            # Создаём бэкап перед изменением
            self.backup_secrets()
            
            # Сохраняем обновлённые секреты
            secrets_loader.save_secrets_to_s3(data)
            logger.info(f"✅ Секрет {secret_name} обновлён")
        else:
            raise ValueError(f"Секрет {secret_name} не найден")


# Глобальный экземпляр менеджера секретов
secrets_manager = SecretsManager()


class EnvironmentSecrets:
    """
    Класс для работы с секретами окружения
    Поддерживает загрузку из .env, S3, или локального файла
    """
    
    def __init__(self):
        self._secrets = {}
        self._load_all_secrets()
    
    def _load_all_secrets(self):
        """Загрузка секретов из всех источников"""
        # 1. Из S3
        try:
            s3_secrets = secrets_manager.load_secrets_from_s3()
            self._secrets.update(s3_secrets)
            logger.info(f"✅ Загружено {len(s3_secrets)} секретов из S3")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить секреты из S3: {e}")
        
        # 2. Из .env (переопределяют S3)
        env_secrets = {
            "SECRET_KEY": settings.secret_key.get_secret_value(),
            "DB_PASSWORD": settings.db_password.get_secret_value(),
            "MINIO_SECRET_KEY": settings.minio_secret_key.get_secret_value(),
        }
        for key, value in env_secrets.items():
            if value and value != "change-me-in-production":
                self._secrets[key] = value
        
        # 3. Локальный файл секретов (для разработки)
        local_secrets_file = Path("secrets.local.json")
        if local_secrets_file.exists():
            with open(local_secrets_file) as f:
                local_secrets = json.load(f)
                self._secrets.update(local_secrets)
                logger.info(f"✅ Загружено {len(local_secrets)} секретов из local файла")
    
    def get(self, key: str, default: str = None) -> str:
        """Получение секрета по ключу"""
        return self._secrets.get(key, default)
    
    def set(self, key: str, value: str, save_to_s3: bool = False):
        """Установка секрета"""
        self._secrets[key] = value
        
        if save_to_s3:
            secrets_manager.save_secrets_to_s3({key: value})
    
    def get_all(self) -> Dict[str, str]:
        """Получение всех секретов"""
        return self._secrets.copy()
    
    def export_to_env(self, env_file: Path = Path(".env")):
        """Экспорт секретов в .env файл"""
        with open(env_file, "w") as f:
            f.write("# Generated by secrets manager\n")
            for key, value in self._secrets.items():
                f.write(f"{key}={value}\n")
        logger.info(f"✅ Секреты экспортированы в {env_file}")


# Глобальный экземпляр
env_secrets = EnvironmentSecrets()