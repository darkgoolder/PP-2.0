from pydantic_settings import BaseSettings
from pathlib import Path
import os
from typing import List, Set


class Settings(BaseSettings):
    """Настройки приложения"""

    # Базовые настройки
    PROJECT_NAME: str = "Wagon Classifier API"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Пути
    BASE_DIR: Path = Path(__file__).parent.parent
    MODEL_PATH: Path = BASE_DIR / "models" / "best_model.pth"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"

    # Настройки для CI/CD (можно переопределить через .env)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        (
            "*"
            if os.getenv("ENVIRONMENT", "development") == "development"
            else "https://yourdomain.com"
        ),
    ]

    # Настройки изображений
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB (добавлено)
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png"}

    # Классы модели (добавлено)
    CLASS_NAMES: List[str] = ["pered", "zad", "none"]
    NUM_CLASSES: int = 3

    # Для тестов
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Создаем необходимые директории
settings.UPLOAD_DIR.mkdir(exist_ok=True)
(settings.BASE_DIR / "models").mkdir(exist_ok=True)
