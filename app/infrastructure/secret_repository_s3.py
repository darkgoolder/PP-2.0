import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class S3SecretRepository:
    """Реализация репозитория секретов в S3"""
    
    def __init__(self, storage, encryption, bucket: str = None, secrets_path: str = None):
        self.storage = storage
        self.encryption = encryption
        self.bucket = bucket or settings.secrets_bucket
        self.secrets_path = secrets_path or settings.secrets_s3_path
        logger.info(f"S3SecretRepository инициализирован: bucket={self.bucket}, path={self.secrets_path}")
    
    async def _load_batch(self) -> Optional[Dict[str, Any]]:
        """Загрузка всех секретов из S3"""
        data = await self.storage.get_object(self.bucket, self.secrets_path)
        if data is None:
            logger.info("Секреты не найдены, будет создан новый файл")
            return None
        
        try:
            return json.loads(data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None
    
    async def _save_batch(self, batch: Dict[str, Any]) -> bool:
        """Сохранение всех секретов в S3"""
        batch["updated_at"] = datetime.now().isoformat()
        data = json.dumps(batch, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Сохранение {len(batch.get('secrets', {}))} секретов")
        return await self.storage.put_object(self.bucket, self.secrets_path, data.encode('utf-8'))
    
    async def save_secret(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Сохранить один секрет"""
        logger.info(f"Сохранение секрета: {key}")
        batch = await self._load_batch()
        if batch is None:
            batch = {
                "version": "1.0",
                "environment": settings.app_env,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "secrets": {}
            }
        
        if encrypt:
            value = self.encryption.encrypt(value)
        
        batch["secrets"][key] = value
        return await self._save_batch(batch)
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Получить секрет по ключу (расшифрованный)"""
        logger.info(f"Получение секрета: {key}")
        batch = await self._load_batch()
        if batch is None or key not in batch.get("secrets", {}):
            logger.warning(f"Секрет не найден: {key}")
            return None
        
        encrypted_value = batch["secrets"][key]
        try:
            return self.encryption.decrypt(encrypted_value)
        except Exception as e:
            logger.error(f"Ошибка расшифровки {key}: {e}")
            return None
    
    async def delete_secret(self, key: str) -> bool:
        """Удалить секрет"""
        logger.info(f"Удаление секрета: {key}")
        batch = await self._load_batch()
        if batch is None or key not in batch.get("secrets", {}):
            return False
        
        del batch["secrets"][key]
        return await self._save_batch(batch)
    
    async def list_secret_keys(self) -> List[str]:
        """Список всех ключей секретов"""
        batch = await self._load_batch()
        if batch is None:
            return []
        return list(batch.get("secrets", {}).keys())
    
    async def get_all_secrets(self) -> Dict[str, str]:
        """Получить все секреты (расшифрованные)"""
        batch = await self._load_batch()
        if batch is None:
            return {}
        
        secrets = {}
        for key, encrypted_value in batch.get("secrets", {}).items():
            try:
                secrets[key] = self.encryption.decrypt(encrypted_value)
            except Exception as e:
                logger.error(f"Ошибка расшифровки {key}: {e}")
                secrets[key] = f"[ERROR: {e}]"
        return secrets


# Глобальный экземпляр (будет создан после импорта s3_storage и encryption_service)
secret_repository = None

def init_secret_repository(storage, encryption):
    """Инициализация глобального репозитория"""
    global secret_repository
    secret_repository = S3SecretRepository(storage, encryption)
    return secret_repository
