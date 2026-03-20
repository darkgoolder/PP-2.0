"""
Конфигурация приложения
Загружает настройки из переменных окружения
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
UPLOAD_DIR = BASE_DIR / "uploads"

# Создаем необходимые папки
UPLOAD_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API настройки
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Wagon Classification API"
    VERSION: str = "1.0.0"
    
    # Модель
    MODEL_PATH: str = str(MODEL_DIR / "best_model.pth")
    CLASS_NAMES: List[str] = ["pered", "zad", "none"]
    
    # Безопасность
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".bmp"}
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()