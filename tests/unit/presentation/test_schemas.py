# """
# Unit-тесты для Pydantic схем
# """

# import pytest
# from app.presentation.schemas import (
#     RegisterRequest, RegisterResponse,
#     LoginRequest, LoginResponse,
#     PredictionResponse, HealthResponse
# )


# class TestRegisterRequest:
#     """Тесты схемы регистрации"""
    
#     def test_valid_data_creates_request(self):
#         """Корректные данные — создаёт объект запроса"""
#         # Arrange & Act
#         request = RegisterRequest(
#             username="testuser",
#             email="test@example.com",
#             password="password123"
#         )
        
#         # Assert
#         assert request.username == "testuser"
#         assert request.email == "test@example.com"
#         assert request.password == "password123"
    
#     def test_missing_field_raises_error(self):
#         """Отсутствие обязательного поля — вызывает ошибку валидации"""
#         with pytest.raises(ValueError):
#             RegisterRequest(username="testuser", email="test@example.com")
    
#     def test_username_min_length_validation(self):
#         """Имя пользователя короче 3 символов — ошибка валидации"""
#         with pytest.raises(ValueError):
#             RegisterRequest(username="ab", email="test@test.com", password="123456")
    
#     def test_password_min_length_validation(self):
#         """Пароль короче 6 символов — ошибка валидации"""
#         with pytest.raises(ValueError):
#             RegisterRequest(username="testuser", email="test@test.com", password="12345")


# class TestLoginRequest:
#     """Тесты схемы входа"""
    
#     def test_valid_data_creates_request(self):
#         """Корректные данные — создаёт объект запроса"""
#         request = LoginRequest(username="testuser", password="password123")
#         assert request.username == "testuser"
#         assert request.password == "password123"


# class TestHealthResponse:
#     """Тесты схемы здоровья"""
    
#     def test_response_contains_all_fields(self):
#         """Ответ health — содержит все необходимые поля"""
#         response = HealthResponse(
#             status="healthy",
#             model_loaded=True,
#             device="cpu",
#             version="2.0.0"
#         )
        
#         assert response.status == "healthy"
#         assert response.model_loaded is True
#         assert response.device == "cpu"
#         assert response.version == "2.0.0"



"""
Unit-тесты для Pydantic схем API
Тестирует все схемы: предсказания, ошибки, здоровье, регистрацию, вход, пользователей
"""

import pytest
from datetime import datetime
from app.presentation.schemas import (
    PredictionResponse,
    ErrorResponse,
    HealthResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    BatchPredictionResponse
)


class TestPredictionResponse:
    """Тесты схемы ответа предсказания"""
    
    def test_validData_createsResponse(self):
        """Корректные данные — создаёт объект ответа"""
        # Arrange
        data = {
            "class": "pered",
            "class_name": "передняя часть вагона",
            "confidence": 0.95,
            "probabilities": {"pered": 0.95, "zad": 0.03, "none": 0.02}
        }
        
        # Act
        response = PredictionResponse(
            status="success",
            data=data,
            request_id="test-123"
        )
        
        # Assert
        assert response.status == "success"
        assert response.data["class"] == "pered"
        assert response.request_id == "test-123"
        assert isinstance(response.timestamp, datetime)
    
    def test_response_hasAllRequiredFields(self):
        """Ответ предсказания — содержит все обязательные поля"""
        # Act
        response = PredictionResponse(
            status="success",
            data={"class": "pered", "confidence": 0.95, "probabilities": {}}
        )
        
        # Assert
        assert hasattr(response, "status")
        assert hasattr(response, "data")
        assert hasattr(response, "timestamp")
    
    def test_requestId_isOptional(self):
        """request_id — опциональное поле"""
        # Act
        response = PredictionResponse(
            status="success",
            data={"class": "pered", "confidence": 0.95, "probabilities": {}}
        )
        
        # Assert
        assert response.request_id is None


class TestErrorResponse:
    """Тесты схемы ошибки"""
    
    def test_errorResponse_containsCodeAndMessage(self):
        """Ответ ошибки — содержит код и сообщение"""
        # Arrange
        error_detail = {"code": "INVALID_IMAGE", "message": "Invalid image format"}
        
        # Act
        response = ErrorResponse(status="error", error=error_detail)
        
        # Assert
        assert response.status == "error"
        assert response.error["code"] == "INVALID_IMAGE"
        assert response.error["message"] == "Invalid image format"


class TestHealthResponse:
    """Тесты схемы здоровья"""
    
    def test_healthResponse_containsAllFields(self):
        """Ответ health check — содержит все поля"""
        # Act
        response = HealthResponse(
            status="healthy",
            model_loaded=True,
            device="cuda",
            version="2.0.0"
        )
        
        # Assert
        assert response.status == "healthy"
        assert response.model_loaded is True
        assert response.device == "cuda"
        assert response.version == "2.0.0"
    
    def test_healthResponse_withModelNotLoaded(self):
        """Health check — модель может быть не загружена"""
        # Act
        response = HealthResponse(
            status="healthy",
            model_loaded=False,
            device="cpu",
            version="2.0.0"
        )
        
        # Assert
        assert response.model_loaded is False


class TestRegisterRequest:
    """Тесты запроса регистрации"""
    
    def test_validData_createsRequest(self):
        """Корректные данные — создаёт запрос регистрации"""
        # Act
        request = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="securepass123"
        )
        
        # Assert
        assert request.username == "newuser"
        assert request.email == "new@example.com"
        assert request.password == "securepass123"
    
    def test_usernameMinLength_raisesValidationError(self):
        """Имя пользователя короче 3 символов — ошибка валидации"""
        # Act & Assert
        with pytest.raises(ValueError):
            RegisterRequest(username="ab", email="test@test.com", password="123456")
    
    def test_passwordMinLength_raisesValidationError(self):
        """Пароль короче 6 символов — ошибка валидации"""
        # Act & Assert
        with pytest.raises(ValueError):
            RegisterRequest(username="testuser", email="test@test.com", password="12345")
    
    def test_invalidEmailFormat_createsRequestWithoutValidation(self):
        """Неверный формат email — Pydantic не валидирует email по умолчанию"""
        # Act
        request = RegisterRequest(username="testuser", email="invalid-email", password="123456")
        
        # Assert
        assert request.email == "invalid-email"  # Pydantic пропускает любой email


class TestRegisterResponse:
    """Тесты ответа регистрации"""
    
    def test_response_containsUserData(self):
        """Ответ регистрации — содержит данные пользователя"""
        # Arrange
        user_data = {
            "id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True
        }
        
        # Act
        response = RegisterResponse(
            status="success",
            user=user_data,
            message="User registered successfully"
        )
        
        # Assert
        assert response.status == "success"
        assert response.user["username"] == "testuser"
        assert response.message == "User registered successfully"


class TestLoginRequest:
    """Тесты запроса входа"""
    
    def test_validData_createsRequest(self):
        """Корректные данные — создаёт запрос входа"""
        # Act
        request = LoginRequest(username="testuser", password="password123")
        
        # Assert
        assert request.username == "testuser"
        assert request.password == "password123"


class TestLoginResponse:
    """Тесты ответа входа"""
    
    def test_response_containsUserData(self):
        """Ответ входа — содержит данные пользователя"""
        # Arrange
        user_data = {
            "id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True
        }
        
        # Act
        response = LoginResponse(status="success", user=user_data)
        
        # Assert
        assert response.status == "success"
        assert response.user["username"] == "testuser"


class TestBatchPredictionResponse:
    """Тесты пакетного ответа предсказания"""
    
    def test_batchResponse_containsResultsAndStats(self):
        """Пакетный ответ — содержит результаты и статистику"""
        # Arrange
        results = [
            {"filename": "img1.jpg", "success": True, "result": {"class": "pered"}},
            {"filename": "img2.jpg", "success": False, "error": "Invalid image"}
        ]
        
        # Act
        response = BatchPredictionResponse(
            status="success",
            results=results,
            total=2,
            successful=1
        )
        
        # Assert
        assert response.status == "success"
        assert len(response.results) == 2
        assert response.total == 2
        assert response.successful == 1