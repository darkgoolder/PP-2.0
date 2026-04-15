# config/settings.py
import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Конфигурация с поддержкой загрузки секретов из S3"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ============================================
    # ОКРУЖЕНИЕ
    # ============================================
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    project_name: str = "Wagon Classification API"
    api_v1_prefix: str = "/api/v1"
    
    # ============================================
    # MINIO S3 НАСТРОЙКИ (для хранения секретов)
    # ============================================
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: SecretStr = Field(default=SecretStr("minioadmin123"), env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    minio_region: str = Field(default="us-east-1", env="MINIO_REGION")
    
    # Бакеты
    secrets_bucket: str = Field(default="wagon-secrets", env="SECRETS_BUCKET")
    s3_bucket_images: str = Field(default="wagon-images", env="S3_BUCKET_IMAGES")
    s3_bucket_models: str = Field(default="wagon-models", env="S3_BUCKET_MODELS")
    s3_bucket_backups: str = Field(default="wagon-backups", env="S3_BUCKET_BACKUPS")
    
    # Путь к файлу секретов в S3
    secrets_s3_path: str = Field(default="secrets/encrypted.json", env="SECRETS_S3_PATH")
    
    # ============================================
    # ОСНОВНЫЕ СЕКРЕТЫ (могут быть переопределены из S3)
    # ============================================
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"), env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # ============================================
    # БАЗА ДАННЫХ
    # ============================================
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: SecretStr = Field(default=SecretStr("postgres123"), env="DB_PASSWORD")
    db_name: str = Field(default="wagon_db", env="DB_NAME")
    db_type: str = Field(default="sqlite", env="DB_TYPE")
    sqlite_path: Path = Field(default="./data/wagon.db", env="SQLITE_PATH")
    
    # ============================================
    # REDIS
    # ============================================
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # ============================================
    # API КЛЮЧИ
    # ============================================
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    admin_api_token: Optional[SecretStr] = Field(default=None, env="ADMIN_API_TOKEN")
    
    # ============================================
    # ML МОДЕЛЬ
    # ============================================
    model_path: Path = Field(default="./models/best_model.pth", env="MODEL_PATH")
    class_names: str = Field(default="pered,zad,none", env="CLASS_NAMES")
    max_upload_size: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")
    allowed_extensions: str = Field(default=".jpg,.jpeg,.png,.bmp", env="ALLOWED_EXTENSIONS")
    
    # ============================================
    # ЛОГИРОВАНИЕ
    # ============================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ============================================
    # ВЫЧИСЛЯЕМЫЕ СВОЙСТВА
    # ============================================
    
    @property
    def class_names_list(self) -> list:
        return [c.strip() for c in self.class_names.split(",")]
    
    @property
    def num_classes(self) -> int:
        return len(self.class_names_list)
    
    @property
    def allowed_extensions_set(self) -> set:
        return set(ext.strip().lower() for ext in self.allowed_extensions.split(","))
    
    @property
    def device(self) -> str:
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
    
    @property
    def database_url(self) -> str:
        """URL для подключения к БД"""
        if self.db_type == "sqlite":
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        else:
            password = self.db_password.get_secret_value()
            return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        """URL для Redis"""
        if self.redis_password:
            password = self.redis_password.get_secret_value()
            return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def minio_config(self) -> dict:
        """Конфигурация для MinIO клиента"""
        return {
            "endpoint": self.minio_endpoint,
            "access_key": self.minio_access_key,
            "secret_key": self.minio_secret_key.get_secret_value(),
            "secure": self.minio_secure,
            "region": self.minio_region,
        }
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    def validate_file_extension(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions_set
    
    def get_class_index(self, class_name: str) -> int:
        try:
            return self.class_names_list.index(class_name)
        except ValueError:
            raise ValueError(f"Class '{class_name}' not found")


# ============================================
# ЗАГРУЗЧИК СЕКРЕТОВ ИЗ S3
# ============================================

class SecretsLoader:
    """Загрузчик секретов из S3 (MinIO)"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._s3_client = None
        self._secrets = {}
    
    @property
    def s3_client(self):
        """Ленивая инициализация S3 клиента"""
        if self._s3_client is None:
            from minio import Minio
            self._s3_client = Minio(
                endpoint=self.settings.minio_endpoint,
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key.get_secret_value(),
                secure=self.settings.minio_secure,
                region=self.settings.minio_region
            )
        return self._s3_client
    
    def load_secrets_from_s3(self) -> Dict[str, str]:
        """Загрузка секретов из S3 бакета"""
        try:
            if not self.s3_client.bucket_exists(self.settings.secrets_bucket):
                logger.warning(f"Бакет {self.settings.secrets_bucket} не существует")
                return {}
            
            response = self.s3_client.get_object(
                bucket_name=self.settings.secrets_bucket,
                object_name=self.settings.secrets_s3_path
            )
            
            secrets_data = json.loads(response.read())
            logger.info(f"✅ Загружено {len(secrets_data)} секретов из S3")
            return secrets_data
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить секреты из S3: {e}")
            return {}
    
    def save_secrets_to_s3(self, secrets: Dict[str, str]):
        """Сохранение секретов в S3 бакет"""
        try:
            if not self.s3_client.bucket_exists(self.settings.secrets_bucket):
                self.s3_client.make_bucket(self.settings.secrets_bucket)
                logger.info(f"✅ Создан бакет: {self.settings.secrets_bucket}")
            
            self.s3_client.put_object(
                bucket_name=self.settings.secrets_bucket,
                object_name=self.settings.secrets_s3_path,
                data=json.dumps(secrets, indent=2).encode(),
                length=len(json.dumps(secrets))
            )
            logger.info(f"✅ Секреты сохранены в S3: {self.settings.secrets_s3_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения секретов в S3: {e}")
            raise


# Глобальный экземпляр настроек
settings = Settings()

# Загрузчик секретов
secrets_loader = SecretsLoader(settings)

# Загружаем секреты из S3 (если доступно)
_s3_secrets = secrets_loader.load_secrets_from_s3()

# Применяем загруженные секреты к настройкам
for key, value in _s3_secrets.items():
    if hasattr(settings, key.lower()):
        current_value = getattr(settings, key.lower())
        if isinstance(current_value, SecretStr):
            setattr(settings, key.lower(), SecretStr(value))
        else:
            setattr(settings, key.lower(), value)
        logger.info(f"✅ Секрет {key} загружен из S3")


def get_settings() -> Settings:
    """Возвращает настройки"""
    return settings


def reload_secrets():
    """Перезагрузка секретов из S3"""
    global _s3_secrets
    _s3_secrets = secrets_loader.load_secrets_from_s3()
    for key, value in _s3_secrets.items():
        if hasattr(settings, key.lower()):
            setattr(settings, key.lower(), SecretStr(value) if "secret" in key.lower() else value)
    logger.info("🔄 Секреты перезагружены из S3")