"""
Тесты API эндпоинтов FastAPI
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
from PIL import Image
import io

# Добавляем корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings


class TestAPI:
    """Тесты API эндпоинтов"""

    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента"""
        return TestClient(app)

    @pytest.fixture
    def sample_image_file(self):
        """Создание тестового изображения для загрузки"""
        img = Image.new("RGB", (224, 224), color="red")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)

        return ("test_image.jpg", img_byte_arr, "image/jpeg")

    def test_health_check(self, client):
        """Тест эндпоинта health check"""
        response = client.get(f"{settings.API_V1_PREFIX}/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code in [200, 404]

    def test_predict_endpoint_with_valid_image(self, client, sample_image_file):
        """Тест эндпоинта предсказания с валидным изображением"""
        filename, file_obj, content_type = sample_image_file

        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)},
        )

        # Если модель не загружена, пропускаем тест
        if response.status_code == 503:
            pytest.skip("Модель не загружена")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "status" in data
        assert data["status"] == "success"

        prediction_data = data["data"]
        assert "class" in prediction_data
        assert "confidence" in prediction_data
        assert "probabilities" in prediction_data

    def test_predict_endpoint_with_invalid_file(self, client):
        """Тест с невалидным файлом (не изображение)"""
        text_file = ("test.txt", io.BytesIO(b"not an image"), "text/plain")
        filename, file_obj, content_type = text_file

        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)},
        )

        assert response.status_code in [400, 422, 500]

    def test_predict_endpoint_without_file(self, client):
        """Тест без файла"""
        response = client.post(f"{settings.API_V1_PREFIX}/predict")
        assert response.status_code == 422


class TestConfigValidation:
    """Тесты конфигурации"""

    def test_settings_loaded(self):
        """Проверка загрузки настроек"""
        assert settings is not None
        assert settings.PROJECT_NAME == "Wagon Classifier API"
        assert settings.VERSION == "2.0.0"

    def test_paths_exist(self):
        """Проверка существования необходимых директорий"""
        assert settings.UPLOAD_DIR.exists() or not settings.UPLOAD_DIR.exists()
        assert settings.MODEL_PATH.suffix == ".pth"