# services/s3_client.py
from minio import Minio
from minio.error import S3Error
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import timedelta
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Клиент для работы с MinIO S3"""
    
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
        logger.info(f"✅ S3 клиент инициализирован: {settings.minio_endpoint}")
    
    def _ensure_buckets(self):
        """Создание бакетов если не существуют"""
        buckets = [
            settings.secrets_bucket,
            settings.s3_bucket_images,
            settings.s3_bucket_models,
            settings.s3_bucket_backups
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"✅ Создан бакет: {bucket}")
            except Exception as e:
                logger.error(f"❌ Ошибка создания бакета {bucket}: {e}")
    
    def upload_file(self, file_path: Path, bucket: str, object_name: Optional[str] = None) -> str:
        """Загрузка файла в S3"""
        if object_name is None:
            object_name = file_path.name
        
        try:
            self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=str(file_path)
            )
            logger.info(f"✅ Загружен: {object_name} -> {bucket}")
            return object_name
        except S3Error as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            raise
    
    def download_file(self, bucket: str, object_name: str, file_path: Path) -> bool:
        """Скачивание файла из S3"""
        try:
            self.client.fget_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=str(file_path)
            )
            logger.info(f"✅ Скачан: {object_name} -> {file_path}")
            return True
        except S3Error as e:
            logger.error(f"❌ Ошибка скачивания: {e}")
            return False
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """Удаление файла из S3"""
        try:
            self.client.remove_object(
                bucket_name=bucket,
                object_name=object_name
            )
            logger.info(f"✅ Удалён: {object_name} из {bucket}")
            return True
        except S3Error as e:
            logger.error(f"❌ Ошибка удаления: {e}")
            return False
    
    def list_files(self, bucket: str, prefix: str = "") -> List[str]:
        """Список файлов в бакете"""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"❌ Ошибка получения списка: {e}")
            return []
    
    def get_presigned_url(self, bucket: str, object_name: str, expires_hours: int = 24) -> str:
        """Получение временной ссылки на файл"""
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except S3Error as e:
            logger.error(f"❌ Ошибка получения URL: {e}")
            raise
    
    def file_exists(self, bucket: str, object_name: str) -> bool:
        """Проверка существования файла"""
        try:
            self.client.stat_object(bucket_name=bucket, object_name=object_name)
            return True
        except S3Error:
            return False


# Глобальный экземпляр
s3_client = S3Client()