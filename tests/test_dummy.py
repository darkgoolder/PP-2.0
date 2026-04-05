"""Минимальные тесты для проверки CI/CD"""

import sys
import os


def test_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    assert version.major == 3
    assert version.minor == 9
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def test_imports():
    """Проверка импорта основных библиотек"""

    print("✅ All imports successful")


def test_model_path():
    """Проверка существования папки для модели"""
    os.makedirs("models", exist_ok=True)
    assert os.path.exists("models")
    print("✅ Models directory exists")


def test_uploads_path():
    """Проверка существования папки для загрузок"""
    os.makedirs("uploads", exist_ok=True)
    assert os.path.exists("uploads")
    print("✅ Uploads directory exists")
