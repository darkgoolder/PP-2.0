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

# Базовые пути - вычисляем динамически при каждом обращении
def get_base_dir():
    """Получаем корневую директорию проекта"""
    return Path(__file__).resolve().parent.parent

def get_model_dir():
    """Получаем директорию с моделью"""
    # Сначала проверяем переменную окружения
    if os.getenv("MODEL_DIR"):
        return Path(os.getenv("MODEL_DIR"))
    return get_base_dir() / "models"

def get_upload_dir():
    """Получаем директорию для загрузок"""
    if os.getenv("UPLOAD_DIR"):
        return Path(os.getenv("UPLOAD_DIR"))
    return get_base_dir() / "uploads"


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API настройки
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Wagon Classification API"
    VERSION: str = "1.0.0"
    
    # Модель
    MODEL_PATH: str = None  # Будет установлено в __init__
    CLASS_NAMES: List[str] = ["pered", "zad", "none"]
    
    # Безопасность
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".bmp"}
    
    # CORS - для HF Spaces нужно добавить URL
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:7860",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:7860",
        "*"  # Для публичного доступа на HF Spaces
    ]
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Устанавливаем MODEL_PATH после инициализации
        if self.MODEL_PATH is None:
            self.MODEL_PATH = str(get_model_dir() / "best_model.pth")
        
        # Создаем директории, если их нет
        get_model_dir().mkdir(exist_ok=True)
        get_upload_dir().mkdir(exist_ok=True)


settings = Settings()