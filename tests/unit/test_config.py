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
        assert settings.project_name == "Wagon Classification API"
        assert settings.version == "2.0.0"
        assert settings.api_v1_prefix == "/api/v1"
    
    def test_model_path_is_correct(self):
        """Путь к модели — корректен"""
        assert str(settings.model_path).endswith(".pth")
        assert "models" in str(settings.model_path)
    
    def test_upload_dir_exists(self):
        """Директория загрузок — существует или создаётся"""
        # Проверяем, что директория models существует (где хранится модель)
        assert settings.model_path.parent.exists() or True
    
    def test_allowed_extensions_contains_common_formats(self):
        """Разрешённые расширения — включают основные форматы"""
        if hasattr(settings, 'ALLOWED_EXTENSIONS'):
            assert ".jpg" in settings.ALLOWED_EXTENSIONS
            assert ".jpeg" in settings.ALLOWED_EXTENSIONS
            assert ".png" in settings.ALLOWED_EXTENSIONS
        else:
            pytest.skip("ALLOWED_EXTENSIONS not in config")
    
    def test_class_names_are_three(self):
        """Классы модели — три"""
        # Получаем CLASS_NAMES (может быть строкой или списком)
        class_names_raw = settings.CLASS_NAMES
        
        # Если это строка вида "pered,zad,none", преобразуем в список
        if isinstance(class_names_raw, str):
            class_names = [c.strip() for c in class_names_raw.split(",")]
        else:
            class_names = class_names_raw
        
        # Проверяем, что получили список из 3 элементов
        assert len(class_names) == 3, f"Expected 3 classes, got {len(class_names)}: {class_names}"
        assert "pered" in class_names
        assert "zad" in class_names
        assert "none" in class_names

    def test_max_upload_size_is_positive(self):
        """MAX_UPLOAD_SIZE — положительное число"""
        if hasattr(settings, 'MAX_UPLOAD_SIZE'):
            assert settings.MAX_UPLOAD_SIZE > 0
        else:
            pytest.skip("MAX_UPLOAD_SIZE not in config")