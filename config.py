# config.py
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal, List
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Конфигурация проекта классификации вагонов"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )
    
    # ============================================
    # ОКРУЖЕНИЕ
    # ============================================
    app_env: Literal["dev", "staging", "production", "testing"] = Field(
        default="dev", env="APP_ENV"
    )
    debug: bool = Field(default=False, env="DEBUG")
    
    # ============================================
    # API
    # ============================================
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    api_title: str = Field(default="Wagon Classification API", env="API_TITLE")
    api_version: str = Field(default="2.0.0", env="API_VERSION")
    
    # ============================================
    # БЕЗОПАСНОСТЬ
    # ============================================
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"), env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # ============================================
    # ML МОДЕЛЬ
    # ============================================
    model_path: Path = Field(default="./models/best_model.pth", env="MODEL_PATH")
    class_names: str = Field(default="pered,zad,none", env="CLASS_NAMES")
    
    @property
    def class_names_list(self) -> List[str]:
        return [name.strip() for name in self.class_names.split(",")]
    
    @property
    def num_classes(self) -> int:
        return len(self.class_names_list)
    
    # ============================================
    # ЗАГРУЗКА ФАЙЛОВ
    # ============================================
    max_upload_size: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")
    allowed_extensions: str = Field(default=".jpg,.jpeg,.png,.bmp", env="ALLOWED_EXTENSIONS")
    
    @property
    def allowed_extensions_set(self) -> set:
        return set(ext.strip().lower() for ext in self.allowed_extensions.split(","))
    
    @property
    def max_upload_size_mb(self) -> float:
        return self.max_upload_size / (1024 * 1024)
    
    # ============================================
    # CORS
    # ============================================
    allowed_origins: List[str] = Field(
        default=["http://localhost", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # ============================================
    # БАЗА ДАННЫХ
    # ============================================
    database_url: str = Field(
        default="postgresql+asyncpg://wagon_user:wagon_pass@localhost:5432/wagon_db",
        env="DATABASE_URL"
    )
    database_url_sync: str = Field(
        default="postgresql://wagon_user:wagon_pass@localhost:5432/wagon_db",
        env="DATABASE_URL_SYNC"
    )
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    # ============================================
    # ЛОГИРОВАНИЕ
    # ============================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", env="LOG_LEVEL")
    
    # ============================================
    # УСТРОЙСТВО ДЛЯ ML
    # ============================================
    @property
    def device(self) -> str:
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "dev"
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"
    
    # ============================================
    # МЕТОДЫ
    # ============================================
    
    @field_validator("model_path", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        path = Path(v)
        if not path.is_absolute():
            path = Path(__file__).parent / path
        return path.resolve()
    
    def validate_file_extension(self, filename: str) -> bool:
        """Проверка расширения файла"""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions_set
    
    def get_class_index(self, class_name: str) -> int:
        """Получение индекса класса по имени"""
        try:
            return self.class_names_list.index(class_name)
        except ValueError:
            raise ValueError(f"Class '{class_name}' not found in {self.class_names_list}")
    
    def model_post_init(self, __context):
        """Проверки после инициализации"""
        if self.app_env == "production" and self.debug:
            raise ValueError("DEBUG cannot be True in production!")
        
        # Создаем директорию для модели если её нет
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Config loaded (env: {self.app_env}, device: {self.device})")


# ============================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР - ЭТО САМОЕ ВАЖНОЕ!
# ============================================

try:
    # СОЗДАЕМ ГЛОБАЛЬНЫЙ ОБЪЕКТ settings
    settings = Settings()
    logger.info(f"✅ Config loaded successfully (env: {settings.app_env})")
except Exception as e:
    logger.error(f"❌ Failed to load config: {e}")
    raise


# Функция для получения настроек
def get_settings() -> Settings:
    """Возвращает глобальный экземпляр настроек"""
    return settings


# Для удобства, чтобы можно было импортировать Config как settings
Config = settings