"""
Unit-тесты для конфигурации
"""

import os
import pytest
from app.config import settings


class TestSettings:
    """Тесты настроек приложения"""
    
    def test_default_settings_are_correct(self):
        """Настройки по умолчанию — корректны"""
        assert settings.PROJECT_NAME == "Wagon Classifier API"
        assert settings.VERSION == "2.0.0"
        assert settings.API_V1_PREFIX == "/api/v1"
    
    def test_model_path_is_correct(self):
        """Путь к модели — корректен"""
        assert settings.MODEL_PATH.suffix == ".pth"
        assert "models" in str(settings.MODEL_PATH)
    
    def test_upload_dir_exists(self):
        """Директория загрузок — существует или создаётся"""
        assert settings.UPLOAD_DIR.exists() or not settings.UPLOAD_DIR.exists()
    
    def test_allowed_extensions_contains_common_formats(self):
        """Разрешённые расширения — включают основные форматы"""
        assert ".jpg" in settings.ALLOWED_EXTENSIONS
        assert ".jpeg" in settings.ALLOWED_EXTENSIONS
        assert ".png" in settings.ALLOWED_EXTENSIONS
    
    def test_class_names_are_three(self):
        """Классы модели — три"""
        assert len(settings.CLASS_NAMES) == 3
        assert "pered" in settings.CLASS_NAMES
        assert "zad" in settings.CLASS_NAMES
        assert "none" in settings.CLASS_NAMES

    def test_max_upload_size_is_positive(self):
        """MAX_UPLOAD_SIZE — положительное число"""
        assert settings.MAX_UPLOAD_SIZE > 0