from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional, List


class Settings(BaseSettings):
    """Конфигурация приложения"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Окружение
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    project_name: str = "Wagon Classification API"
    version: str = "2.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Модель
    model_path: str = Field(default="./models/best_model.pth", env="MODEL_PATH")
    
    # MinIO S3
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: SecretStr = Field(default=SecretStr("minioadmin123"), env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    minio_region: str = Field(default="us-east-1", env="MINIO_REGION")
    
    # Бакеты
    secrets_bucket: str = Field(default="wagon-secrets", env="SECRETS_BUCKET")
    secrets_s3_path: str = Field(default="secrets/encrypted.json", env="SECRETS_S3_PATH")
    
    # Безопасность
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"), env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    admin_api_token: Optional[SecretStr] = Field(default=None, env="ADMIN_API_TOKEN")
    
    # База данных
    db_type: str = Field(default="sqlite", env="DB_TYPE")
    sqlite_path: Path = Field(default="./data/wagon.db", env="SQLITE_PATH")
    
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


settings = Settings()