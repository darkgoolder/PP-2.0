from pathlib import Path
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения - все креды из переменных окружения"""

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
    version: str = "2.0.0"
    api_v1_prefix: str = "/api/v1"

    # ============================================
    # ЛОГИРОВАНИЕ
    # ============================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ============================================
    # МОДЕЛЬ
    # ============================================
    model_path: str = Field(default="./models/best_model.pth", env="MODEL_PATH")
    MODEL_PATH: str = Field(default="./models/best_model.pth", env="MODEL_PATH")
    class_names: str = Field(default="pered,zad,none", env="CLASS_NAMES")
    CLASS_NAMES: str = Field(default="pered,zad,none", env="CLASS_NAMES")

    # ============================================
    # MINIO S3
    # ============================================
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: SecretStr = Field(..., env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    minio_region: str = Field(default="us-east-1", env="MINIO_REGION")

    # ============================================
    # БАКЕТЫ
    # ============================================
    secrets_bucket: str = Field(default="wagon-secrets", env="SECRETS_BUCKET")
    secrets_s3_path: str = Field(
        default="secrets/encrypted.json", env="SECRETS_S3_PATH"
    )

    # ============================================
    # БЕЗОПАСНОСТЬ (JWT)
    # ============================================
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    admin_api_token: Optional[SecretStr] = Field(default=None, env="ADMIN_API_TOKEN")

    # ============================================
    # БАЗА ДАННЫХ
    # ============================================
    db_type: str = Field(default="sqlite", env="DB_TYPE")
    sqlite_path: Path = Field(default="./data/wagon.db", env="SQLITE_PATH")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")

    # ============================================
    # СВОЙСТВА
    # ============================================

    @property
    def class_names_list(self) -> List[str]:
        return [c.strip() for c in self.class_names.split(",")]

    @property
    def num_classes(self) -> int:
        return len(self.class_names_list)

    @property
    def minio_config(self) -> dict:
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

    @property
    def device(self) -> str:
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    @property
    def ALLOWED_EXTENSIONS(self) -> set:
        return {".jpg", ".jpeg", ".png", ".bmp"}

    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        return 10 * 1024 * 1024

    def validate_file_extension(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS

    def get_class_index(self, class_name: str) -> int:
        try:
            return self.class_names_list.index(class_name)
        except ValueError:
            raise ValueError(f"Class '{class_name}' not found")


settings = Settings()
