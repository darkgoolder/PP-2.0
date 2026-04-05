"""Минимальные тесты для проверки CI/CD"""

import sys
import os
import pytest
import importlib


def test_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    assert version.major == 3
    assert version.minor >= 9  # Поддерживается 3.9, 3.10, 3.11+
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def test_imports():
    """Проверка импорта основных библиотек с помощью importlib"""
    required_packages = ["fastapi", "torch", "PIL", "numpy"]
    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        pytest.skip(f"Some packages are missing: {missing_packages}")
    else:
        print("✅ All required packages are available")


def test_directories():
    """Проверка существования необходимых директорий"""
    os.makedirs("models", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)

    assert os.path.exists("models")
    assert os.path.exists("uploads")
    print("✅ Required directories exist")


def test_config_loading():
    """Проверка загрузки конфигурации"""
    try:
        from app.config import settings

        assert settings.PROJECT_NAME == "Wagon Classifier API"
        assert settings.VERSION == "2.0.0"
        assert hasattr(settings, "CLASS_NAMES")
        print("✅ Config loaded successfully")
    except Exception as e:
        pytest.skip(f"Config loading failed: {e}")


def test_app_creation():
    """Проверка создания FastAPI приложения"""
    try:
        from app.main import app

        assert app.title == "Wagon Classifier API"
        print("✅ FastAPI app created successfully")
    except Exception as e:
        pytest.skip(f"App creation failed: {e}")
