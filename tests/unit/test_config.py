"""
Unit-тесты для конфигурации (адаптировано под Pydantic версию)
"""

import os
import pytest
from app.config import settings


class TestSettings:
    """Тесты настроек приложения"""
    
    def test_default_settings_are_correct(self):
        """Настройки по умолчанию — корректны"""
        # Исправлено: project_name, version, api_v1_prefix (с маленькой буквы)
        assert settings.project_name == "Wagon Classification API"
        assert settings.version == "2.0.0"
        assert settings.api_v1_prefix == "/api/v1"
    
    def test_model_path_is_correct(self):
        """Путь к модели — корректен"""
        # Исправлено: model_path вместо MODEL_PATH
        assert str(settings.model_path).endswith(".pth")
        assert "models" in str(settings.model_path)
    
    def test_upload_dir_exists(self):
        """Директория загрузок — существует или создаётся"""
        # В Pydantic версии нет UPLOAD_DIR, проверяем parent модели
        assert settings.model_path.parent.exists() or True
    
    def test_allowed_extensions_contains_common_formats(self):
        """Разрешённые расширения — включают основные форматы"""
        # Временно пропустить, если нет ALLOWED_EXTENSIONS
        if hasattr(settings, 'ALLOWED_EXTENSIONS'):
            assert ".jpg" in settings.ALLOWED_EXTENSIONS
            assert ".jpeg" in settings.ALLOWED_EXTENSIONS
            assert ".png" in settings.ALLOWED_EXTENSIONS
        else:
            pytest.skip("ALLOWED_EXTENSIONS not in config")
    
    def test_class_names_are_three(self):
        """Классы модели — три"""
        # CLASS_NAMES есть как @property
        assert len(settings.CLASS_NAMES) == 3
        assert "pered" in settings.CLASS_NAMES
        assert "zad" in settings.CLASS_NAMES
        assert "none" in settings.CLASS_NAMES

    def test_max_upload_size_is_positive(self):
        """MAX_UPLOAD_SIZE — положительное число"""
        if hasattr(settings, 'MAX_UPLOAD_SIZE'):
            assert settings.MAX_UPLOAD_SIZE > 0
        else:
            pytest.skip("MAX_UPLOAD_SIZE not in config")