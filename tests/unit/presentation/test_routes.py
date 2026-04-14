# """
# Unit-тесты для API роутов (с моками)
# """

# import pytest
# from unittest.mock import AsyncMock, Mock, patch
# from fastapi import HTTPException
# from PIL import Image
# import io


# class TestRoutes:
#     """Тесты API эндпоинтов"""
    
#     @pytest.fixture
#     def mock_classifier(self):
#         """Мок классификатора"""
#         classifier = Mock()
#         classifier.predict = Mock(return_value=("pered", 0.95, {"pered": 0.95, "zad": 0.03, "none": 0.02}))
#         classifier.class_names_ru = {"pered": "передняя часть вагона"}
#         classifier.device = "cpu"
#         return classifier
    
#     @pytest.fixture
#     def mock_get_classifier(self, mock_classifier):
#         """Мок get_classifier"""
#         with patch('app.infrastructure.model_repository.get_classifier', return_value=mock_classifier):
#             yield
    
#     @pytest.fixture
#     def client(self):
#         from fastapi.testclient import TestClient
#         from app.main import app
#         return TestClient(app)
    
#     def test_health_endpoint_returns_200(self, client):
#         """GET /health — возвращает 200 OK"""
#         response = client.get("/api/v1/health")
#         assert response.status_code == 200
    
#     def test_predict_endpoint_requires_file(self, client):
#         """POST /predict без файла — возвращает 422"""
#         response = client.post("/api/v1/predict")
#         assert response.status_code == 422
    
#     def test_predict_endpoint_with_invalid_file_returns_error(self, client):
#         """POST /predict с невалидным файлом — возвращает ошибку"""
#         response = client.post(
#             "/api/v1/predict",
#             files={"file": ("test.txt", b"not an image", "text/plain")}
#         )
#         assert response.status_code in [400, 500]
    
#     def test_predict_batch_endpoint_accepts_multiple_files(self, client):
#         """POST /predict-batch — принимает несколько файлов"""
#         # Создаём тестовое изображение
#         img = Image.new('RGB', (100, 100))
#         img_bytes = io.BytesIO()
#         img.save(img_bytes, format='JPEG')
        
#         response = client.post(
#             "/api/v1/predict-batch",
#             files=[
#                 ("files", ("test1.jpg", img_bytes.getvalue(), "image/jpeg")),
#                 ("files", ("test2.jpg", img_bytes.getvalue(), "image/jpeg"))
#             ]
#         )
#         # Может быть 200 или 503 (если модель не загружена)
#         assert response.status_code in [200, 503]


"""
Unit-тесты для API роутов (с моками, без реальной БД)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.presentation.api.routes import router
from app.domain.entities import User, UserRole


class TestRoutesMock:
    """Тесты API роутов с моками"""
    
    @pytest.fixture
    def mock_get_db_manager(self):
        """Мок менеджера БД"""
        with patch('app.presentation.api.routes.get_db_manager') as mock:
            mock_manager = Mock()
            mock_manager.get_session = Mock()
            mock.return_value = mock_manager
            yield mock
    
    @pytest.fixture
    def mock_register_use_case(self):
        """Мок use case регистрации"""
        with patch('app.presentation.api.routes.RegisterUserUseCase') as mock:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value={
                "id": "123",
                "username": "testuser",
                "email": "test@test.com",
                "role": "user",
                "is_active": True
            })
            mock.return_value = mock_instance
            yield mock
    
    def test_health_endpoint_returns_200(self):
        """GET /health — возвращает 200 OK"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_correct_structure(self):
        """GET /health — возвращает правильную структуру"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert "status" in data
        assert "model_loaded" in data
        assert "device" in data
        assert "version" in data