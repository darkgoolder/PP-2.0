# config.py - Упрощённая версия (без pydantic)
import os
from pathlib import Path
from typing import List

class Settings:
    """Простая конфигурация проекта"""
    
    def __init__(self):
        # Загружаем .env файл
        self._load_env()
        
        # Основные настройки
        self.app_env = os.getenv("APP_ENV", "dev")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.api_prefix = os.getenv("API_PREFIX", "/api/v1")
        self.api_title = os.getenv("API_TITLE", "Wagon API")
        self.model_path = Path(os.getenv("MODEL_PATH", "./models/best_model.pth"))
        self.class_names = os.getenv("CLASS_NAMES", "pered,zad,none")
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        self.secret_key = os.getenv("SECRET_KEY", "change-me")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Создаём папку для модели
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_env(self):
        """Загрузка .env файла"""
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        os.environ[key.strip()] = val.strip()
    
    @property
    def class_names_list(self) -> List[str]:
        """Список классов"""
        return [c.strip() for c in self.class_names.split(",")]
    
    @property
    def num_classes(self) -> int:
        """Количество классов"""
        return len(self.class_names_list)
    
    @property
    def device(self) -> str:
        """Устройство (CPU/GPU)"""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "dev"
    
    def validate_file_extension(self, filename: str) -> bool:
        """Проверка расширения файла"""
        ext = Path(filename).suffix.lower()
        return ext in {'.jpg', '.jpeg', '.png', '.bmp'}
    
    def get_class_index(self, class_name: str) -> int:
        """Индекс класса по имени"""
        return self.class_names_list.index(class_name)


# Глобальный экземпляр
settings = Settings()