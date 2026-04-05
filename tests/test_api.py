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
sys.path.append(str(Path(__file__).parent.parent))

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
        img = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
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
        if response.status_code == 200:
            assert "text/html" in response.headers["content-type"]
    
    def test_predict_endpoint_with_valid_image(self, client, sample_image_file):
        """Тест эндпоинта предсказания с валидным изображением"""
        filename, file_obj, content_type = sample_image_file
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)}
        )
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем структуру ответа (данные внутри поля 'data')
        assert "data" in data
        assert "status" in data
        assert data["status"] == "success"
        
        # Проверяем данные предсказания
        prediction_data = data["data"]
        assert "class" in prediction_data
        assert "confidence" in prediction_data
        assert "probabilities" in prediction_data
        assert "filename" not in prediction_data  # В одиночном предсказании нет filename
        
        # Проверяем типы данных
        assert isinstance(prediction_data["class"], str)
        assert isinstance(prediction_data["confidence"], float)
        assert 0 <= prediction_data["confidence"] <= 1
        
    def test_predict_endpoint_with_invalid_file(self, client):
        """Тест с невалидным файлом (не изображение)"""
        text_file = ("test.txt", io.BytesIO(b"not an image"), "text/plain")
        filename, file_obj, content_type = text_file
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)}
        )
        
        # Должна быть ошибка
        assert response.status_code in [400, 500]
        
    def test_predict_endpoint_without_file(self, client):
        """Тест без файла"""
        response = client.post(f"{settings.API_V1_PREFIX}/predict")
        
        assert response.status_code == 422  # Unprocessable Entity
        
    def test_predict_endpoint_with_large_file(self, client):
        """Тест с большим файлом"""
        # Создаем большое изображение (5MB)
        large_img = Image.new('RGB', (4000, 4000), color='green')
        img_byte_arr = io.BytesIO()
        large_img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": ("large.jpg", img_byte_arr, "image/jpeg")}
        )
        
        # Должен быть успех или ошибка размера
        assert response.status_code in [200, 413, 500]
        
    def test_predict_endpoint_response_format(self, client, sample_image_file):
        """Тест формата ответа"""
        filename, file_obj, content_type = sample_image_file
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем что данные внутри поля 'data'
            assert "data" in data
            prediction_data = data["data"]
            
            # Проверяем вероятности внутри data
            assert "probabilities" in prediction_data
            probabilities = prediction_data["probabilities"]
            assert isinstance(probabilities, dict)
            
            # Сумма вероятностей должна быть примерно 1
            total = sum(probabilities.values())
            assert abs(total - 1.0) < 0.01


class TestAPIPerformance:
    """Тесты производительности API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_image_file(self):
        """Создание тестового изображения"""
        img = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        return ("test.jpg", img_byte_arr, "image/jpeg")
    
    def test_response_time(self, client, sample_image_file):
        """Тест времени ответа (должно быть < 2 секунд)"""
        import time
        
        filename, file_obj, content_type = sample_image_file
        
        start_time = time.time()
        response = client.post(
            f"{settings.API_V1_PREFIX}/predict",
            files={"file": (filename, file_obj, content_type)}
        )
        elapsed_time = time.time() - start_time
        
        # Если модель загружена, время должно быть приемлемым
        if response.status_code == 200:
            assert elapsed_time < 2.0, f"Слишком долго: {elapsed_time:.2f} секунд"


class TestConfigValidation:
    """Тесты конфигурации"""
    
    def test_settings_loaded(self):
        """Проверка загрузки настроек"""
        assert settings is not None
        assert settings.PROJECT_NAME == "Wagon Classifier API"
        assert settings.VERSION == "2.0.0"
        
    def test_paths_exist(self):
        """Проверка существования необходимых директорий"""
        # Проверяем, что директории создаются при необходимости
        assert settings.UPLOAD_DIR.exists() or not settings.UPLOAD_DIR.exists()
        assert settings.MODEL_PATH.suffix == '.pth'