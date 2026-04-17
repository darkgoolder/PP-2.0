# app/infrastructure/s3_storage.py
import logging
from typing import Optional, List
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """Реализация S3 хранилища через MinIO"""
    
    def __init__(self):
        config = settings.minio_config
        self.client = Minio(
            endpoint=config["endpoint"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=config["secure"],
            region=config["region"]
        )
        self._ensure_buckets()
        logger.info(f"S3StorageService инициализирован: {settings.minio_endpoint}")
    
    def _ensure_buckets(self):
        """Создание бакетов если не существуют"""
        buckets = [settings.secrets_bucket]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Создан бакет: {bucket}")
            except Exception as e:
                logger.error(f"Ошибка создания бакета {bucket}: {e}")
    
    async def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """Получение объекта из S3"""
        try:
            response = self.client.get_object(
                bucket_name=bucket,
                object_name=key
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"Ошибка получения объекта {key}: {e}")
            raise
    
    async def put_object(self, bucket: str, key: str, data: bytes) -> bool:
        """Сохранение объекта в S3"""
        try:
            # Преобразуем bytes в BytesIO для совместимости
            data_stream = BytesIO(data)
            self.client.put_object(
                bucket_name=bucket,
                object_name=key,
                data=data_stream,
                length=len(data),
                content_type='application/json'
            )
            logger.info(f"Сохранён объект: {key}")
            return True
        except S3Error as e:
            logger.error(f"Ошибка сохранения {key}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Удаление объекта из S3"""
        try:
            self.client.remove_object(
                bucket_name=bucket,
                object_name=key
            )
            logger.info(f"Удалён объект: {key}")
            return True
        except S3Error as e:
            logger.error(f"Ошибка удаления {key}: {e}")
            return False
    
    async def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        """Список объектов в бакете"""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Ошибка получения списка: {e}")
            return []
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Проверка существования объекта"""
        try:
            self.client.stat_object(bucket_name=bucket, object_name=key)
            return True
        except S3Error:
            return False


# Глобальный экземпляр
s3_storage = S3StorageService()