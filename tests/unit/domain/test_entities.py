"""
Unit-тесты для доменных сущностей
Соблюдение правил:
- AAA (Arrange-Act-Assert)
- Один тест - одна проверка
- Говорящие имена: [Метод]_[Сценарий]_[Ожидание]
"""

import pytest
from datetime import datetime
from app.domain.entities import User, UserRole, PredictionResult, WagonSide


class TestUser:
    """Тесты сущности User (соответствует правилу: один класс = одна сущность)"""
    
    def test_constructor_withMinimalData_createsUserWithDefaults(self):
        """Конструктор с минимальными данными — создаёт пользователя со значениями по умолчанию"""
        # Arrange
        user_id = "123"
        username = "testuser"
        email = "test@example.com"
        hashed_password = "hashed_123"
        
        # Act
        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        
        # Assert
        assert user.id == user_id
        assert user.username == username
        assert user.email == email
        assert user.hashed_password == hashed_password
        assert user.is_active is True
        assert user.role == UserRole.USER
        assert isinstance(user.created_at, datetime)
    
    def test_toDict_withValidUser_returnsDictWithoutPassword(self):
        """Преобразование в словарь — возвращает все поля кроме пароля"""
        # Arrange
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="secret"
        )
        
        # Act
        result = user.to_dict()
        
        # Assert
        assert result["id"] == "123"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert "hashed_password" not in result
        assert "role" in result
    
    def test_activate_userWasInactive_setsIsActiveToTrue(self):
        """Активация пользователя — меняет статус на активный"""
        # Arrange
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="hash",
            is_active=False
        )
        
        # Act
        user.activate()
        
        # Assert
        assert user.is_active is True
    
    def test_deactivate_userWasActive_setsIsActiveToFalse(self):
        """Деактивация пользователя — меняет статус на неактивный"""
        # Arrange
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="hash",
            is_active=True
        )
        
        # Act
        user.deactivate()
        
        # Assert
        assert user.is_active is False
    
    def test_verifyPassword_correctPassword_returnsTrue(self):
        """Проверка пароля — корректный пароль возвращает True"""
        # Arrange
        class MockHasher:
            def verify(self, password, hashed):
                return password == "correct" and hashed == "stored_hash"
        
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="stored_hash"
        )
        
        # Act
        result = user.verify_password("correct", MockHasher())
        
        # Assert
        assert result is True
    
    def test_verifyPassword_wrongPassword_returnsFalse(self):
        """Проверка пароля — неверный пароль возвращает False"""
        # Arrange
        class MockHasher:
            def verify(self, password, hashed):
                return False
        
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="stored_hash"
        )
        
        # Act
        result = user.verify_password("wrong", MockHasher())
        
        # Assert
        assert result is False


class TestPredictionResult:
    """Тесты сущности PredictionResult"""
    
    def test_constructor_withValidData_createsPredictionResult(self):
        """Конструктор с корректными данными — создаёт объект предсказания"""
        # Arrange
        side = WagonSide.PERED
        confidence = 0.95
        probabilities = {"pered": 0.95, "zad": 0.03, "none": 0.02}
        filename = "test.jpg"
        
        # Act
        result = PredictionResult(
            side=side,
            confidence=confidence,
            probabilities=probabilities,
            image_filename=filename
        )
        
        # Assert
        assert result.side == side
        assert result.confidence == confidence
        assert result.probabilities == probabilities
        assert result.image_filename == filename
        assert result.request_id is not None
    
    def test_classNameRu_forPeredSide_returnsRussianName(self):
        """Русское название — для класса 'pered' возвращает 'передняя часть вагона'"""
        # Arrange
        result = PredictionResult(
            side=WagonSide.PERED,
            confidence=0.95,
            probabilities={},
            image_filename="test.jpg"
        )
        
        # Act
        name = result.class_name_ru
        
        # Assert
        assert name == "передняя часть вагона"
    
    def test_classNameRu_forZadSide_returnsRussianName(self):
        """Русское название — для класса 'zad' возвращает 'задняя часть вагона'"""
        # Arrange
        result = PredictionResult(
            side=WagonSide.ZAD,
            confidence=0.95,
            probabilities={},
            image_filename="test.jpg"
        )
        
        # Act
        name = result.class_name_ru
        
        # Assert
        assert name == "задняя часть вагона"
    
    def test_classNameRu_forNoneSide_returnsRussianName(self):
        """Русское название — для класса 'none' возвращает 'вагон не обнаружен'"""
        # Arrange
        result = PredictionResult(
            side=WagonSide.NONE,
            confidence=0.95,
            probabilities={},
            image_filename="test.jpg"
        )
        
        # Act
        name = result.class_name_ru
        
        # Assert
        assert name == "вагон не обнаружен"
    
    def test_toDict_returnsCompleteDictionaryWithoutRequestId(self):
        """Преобразование в словарь — возвращает все поля предсказания"""
        # Arrange
        result = PredictionResult(
            side=WagonSide.PERED,
            confidence=0.95,
            probabilities={"pered": 0.95},
            image_filename="test.jpg",
            request_id="req-123"
        )
        
        # Act
        data = result.to_dict()
        
        # Assert
        assert data["class"] == "pered"
        assert data["class_name"] == "передняя часть вагона"
        assert data["confidence"] == 0.95
        assert data["probabilities"] == {"pered": 0.95}
        assert "timestamp" in data
        
        
        
class TestDailyReportEntity:
    """Тесты сущности DailyReport"""
    
    def test_daily_report_to_dict_returns_all_fields(self):
        """DailyReport.to_dict() — возвращает все поля"""
        from app.domain.entities import DailyReport
        from datetime import datetime
        
        report_date = datetime(2024, 1, 15, 10, 30, 0)
        report = DailyReport(
            report_date=report_date,
            new_users_count=5,
            total_predictions=100,
            model_exists=True,
            model_accuracy=0.95
        )
        
        data = report.to_dict()
        
        assert data["report_date"] == report_date.isoformat()
        assert data["new_users_count"] == 5
        assert data["total_predictions"] == 100
        assert data["model_exists"] is True
        assert data["model_accuracy"] == 0.95
        assert "report_generated_at" in data


class TestSecretsBatchEntity:
    """Тесты сущности SecretsBatch (строки 132, 134)"""
    
    def test_secrets_batch_from_dict_with_string_dates(self):
        """SecretsBatch.from_dict() — обрабатывает даты в виде строк"""
        from app.domain.entities import SecretsBatch
        
        data = {
            "secrets": {"key": "value"},
            "version": "1.0",
            "environment": "test",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        }
        
        batch = SecretsBatch.from_dict(data)
        
        assert batch.created_at.year == 2024
        assert batch.updated_at.year == 2024