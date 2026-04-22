# # app/config.py
# from pathlib import Path
# from typing import Optional, List
# from pydantic import Field, SecretStr
# from pydantic_settings import BaseSettings, SettingsConfigDict

# import sys
# from pathlib import Path as PathlibPath
# sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

# from config import settings as root_settings


# class Settings(BaseSettings):
#     """Конфигурация приложения - данные из корневого config.py"""

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore",
#     )

#     # ============================================
#     # ОКРУЖЕНИЕ
#     # ============================================
#     app_env: str = Field(default="development", env="APP_ENV")
#     debug: bool = Field(default=True, env="DEBUG")
#     project_name: str = "Wagon Classification API"
#     version: str = "2.0.0"
#     api_v1_prefix: str = "/api/v1"

#     # ============================================
#     # ЛОГИРОВАНИЕ
#     # ============================================
#     log_level: str = Field(default="INFO", env="LOG_LEVEL")

#     # ============================================
#     # МОДЕЛЬ (из корневого config.py)
#     # ============================================
#     @property
#     def model_path(self) -> Path:
#         return root_settings.model_path

#     # ============================================
#     # MINIO S3 (из корневого config.py)
#     # ============================================
#     @property
#     def minio_endpoint(self) -> str:
#         return root_settings.minio_config["endpoint"]

#     @property
#     def minio_access_key(self) -> str:
#         return root_settings.minio_config["access_key"]

#     @property
#     def minio_secret_key(self) -> SecretStr:
#         return SecretStr(root_settings.minio_config["secret_key"])

#     @property
#     def minio_secure(self) -> bool:
#         return root_settings.minio_config["secure"]

#     @property
#     def minio_region(self) -> str:
#         return root_settings.minio_config["region"]

#     # ============================================
#     # БАКЕТЫ (из корневого config.py)
#     # ============================================
#     @property
#     def secrets_bucket(self) -> str:
#         return root_settings.secrets_bucket

#     secrets_s3_path: str = Field(
#         default="secrets/encrypted.json", env="SECRETS_S3_PATH"
#     )

#     # ============================================
#     # БЕЗОПАСНОСТЬ (JWT)
#     # ============================================
#     secret_key: SecretStr = Field(..., env="SECRET_KEY")
#     algorithm: str = Field(default="HS256", env="ALGORITHM")
#     access_token_expire_minutes: int = Field(
#         default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
#     )
#     admin_api_token: Optional[SecretStr] = Field(default=None, env="ADMIN_API_TOKEN")

#     # ============================================
#     # БАЗА ДАННЫХ
#     # ============================================
#     db_type: str = Field(default="sqlite", env="DB_TYPE")
#     sqlite_path: Path = Field(default="./data/wagon.db", env="SQLITE_PATH")

#     # ============================================
#     # СВОЙСТВА
#     # ============================================

#     @property
#     def minio_config(self) -> dict:
#         return root_settings.minio_config

#     @property
#     def is_development(self) -> bool:
#         return self.app_env == "development"

#     @property
#     def is_production(self) -> bool:
#         return self.app_env == "production"

#     @property
#     def CLASS_NAMES(self) -> List[str]:
#         """Список классов для модели"""
#         return root_settings.CLASS_NAMES

#     @property
#     def class_names_list(self) -> List[str]:
#         return root_settings.class_names_list

#     @property
#     def num_classes(self) -> int:
#         return root_settings.num_classes

#     @property
#     def device(self) -> str:
#         return root_settings.device

#     def validate_file_extension(self, filename: str) -> bool:
#         return root_settings.validate_file_extension(filename)

#     def get_class_index(self, class_name: str) -> int:
#         return root_settings.get_class_index(class_name)


# settings = Settings()


# app/config.py
import importlib.util
from pathlib import Path
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Загружаем корневой config.py через абсолютный путь
root_config_path = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("root_config", root_config_path)
root_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_config)
root_settings = root_config.settings


class Settings(BaseSettings):
    """Конфигурация приложения - данные из корневого config.py"""

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
    # МОДЕЛЬ (из корневого config.py)
    # ============================================
    @property
    def model_path(self) -> Path:
        return root_settings.model_path

    # ============================================
    # MINIO S3 (из корневого config.py)
    # ============================================
    @property
    def minio_endpoint(self) -> str:
        return root_settings.minio_config["endpoint"]

    @property
    def minio_access_key(self) -> str:
        return root_settings.minio_config["access_key"]

    @property
    def minio_secret_key(self) -> SecretStr:
        return SecretStr(root_settings.minio_config["secret_key"])

    @property
    def minio_secure(self) -> bool:
        return root_settings.minio_config["secure"]

    @property
    def minio_region(self) -> str:
        return root_settings.minio_config["region"]

    # ============================================
    # БАКЕТЫ (из корневого config.py)
    # ============================================
    @property
    def secrets_bucket(self) -> str:
        return root_settings.secrets_bucket

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

    # ============================================
    # СВОЙСТВА
    # ============================================

    @property
    def minio_config(self) -> dict:
        return root_settings.minio_config

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def CLASS_NAMES(self) -> List[str]:
        return root_settings.CLASS_NAMES

    @property
    def class_names_list(self) -> List[str]:
        return root_settings.class_names_list

    @property
    def num_classes(self) -> int:
        return root_settings.num_classes

    @property
    def device(self) -> str:
        return root_settings.device

    def validate_file_extension(self, filename: str) -> bool:
        return root_settings.validate_file_extension(filename)

    def get_class_index(self, class_name: str) -> int:
        return root_settings.get_class_index(class_name)

    @property
    def ALLOWED_EXTENSIONS(self) -> set:
        """Разрешённые расширения файлов"""
        return {".jpg", ".jpeg", ".png", ".bmp"}

    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """Максимальный размер загружаемого файла (10 MB)"""
        return 10 * 1024 * 1024


settings = Settings()
