"""
Unit-тесты для доменных исключений
"""

import pytest
from app.domain.exceptions import (
    DomainException,
    InvalidImageException,
    ModelNotFoundException,
    ModelNotLoadedException,
    TrainingException,
    DataPreparationException,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotActiveError
)


class TestDomainExceptions:
    """Тесты доменных исключений"""
    
    def test_domainException_is_base_exception(self):
        """DomainException — базовый класс для всех доменных исключений"""
        # Act & Assert
        with pytest.raises(DomainException):
            raise DomainException("Test error")
    
    def test_invalidImageException_contains_correct_message(self):
        """InvalidImageException — содержит корректное сообщение"""
        # Arrange
        error_message = "Image is corrupted"
        
        # Act & Assert
        with pytest.raises(InvalidImageException) as exc_info:
            raise InvalidImageException(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_modelNotFoundException_contains_correct_message(self):
        """ModelNotFoundException — содержит корректное сообщение"""
        # Arrange
        error_message = "Model not found at path /models/best.pth"
        
        # Act & Assert
        with pytest.raises(ModelNotFoundException) as exc_info:
            raise ModelNotFoundException(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_modelNotLoadedException_has_default_message(self):
        """ModelNotLoadedException — имеет сообщение по умолчанию"""
        # Act & Assert
        with pytest.raises(ModelNotLoadedException) as exc_info:
            raise ModelNotLoadedException()
        
        assert "Модель не загружена" in str(exc_info.value)
    
    def test_trainingException_contains_correct_message(self):
        """TrainingException — содержит корректное сообщение"""
        # Arrange
        error_message = "Training failed due to insufficient data"
        
        # Act & Assert
        with pytest.raises(TrainingException) as exc_info:
            raise TrainingException(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_dataPreparationException_contains_correct_message(self):
        """DataPreparationException — содержит корректное сообщение"""
        # Arrange
        error_message = "Cannot prepare data from archive"
        
        # Act & Assert
        with pytest.raises(DataPreparationException) as exc_info:
            raise DataPreparationException(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_userNotFoundError_contains_correct_message(self):
        """UserNotFoundError — содержит корректное сообщение"""
        # Arrange
        error_message = "User 'john' not found"
        
        # Act & Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            raise UserNotFoundError(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_userAlreadyExistsError_contains_correct_message(self):
        """UserAlreadyExistsError — содержит корректное сообщение"""
        # Arrange
        error_message = "Username 'john' already taken"
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            raise UserAlreadyExistsError(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_invalidCredentialsError_contains_correct_message(self):
        """InvalidCredentialsError — содержит корректное сообщение"""
        # Arrange
        error_message = "Invalid username or password"
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            raise InvalidCredentialsError(error_message)
        
        assert str(exc_info.value) == error_message
    
    def test_userNotActiveError_contains_correct_message(self):
        """UserNotActiveError — содержит корректное сообщение"""
        # Arrange
        error_message = "User account is deactivated"
        
        # Act & Assert
        with pytest.raises(UserNotActiveError) as exc_info:
            raise UserNotActiveError(error_message)
        
        assert str(exc_info.value) == error_message