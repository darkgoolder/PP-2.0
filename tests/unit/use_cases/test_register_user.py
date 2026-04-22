"""
Unit-тесты для use case регистрации пользователя
Соблюдение правил:
- Моки для внешних зависимостей (репозиторий, хешер)
- AAA (Arrange-Act-Assert)
- Один тест - один сценарий
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.use_cases.register_user import RegisterUserUseCase
from app.domain.exceptions import UserAlreadyExistsError, InvalidCredentialsError


class TestRegisterUserUseCase:
    """
    Тесты use case регистрации пользователя
    Имя класса соответствует тестируемой сущности
    """
    
    @pytest.fixture
    def mock_user_repository(self):
        """Фикстура: стаб репозитория (имитирует состояние)"""
        repo = Mock()
        repo.exists_by_username = AsyncMock(return_value=False)
        repo.exists_by_email = AsyncMock(return_value=False)
        repo.save = AsyncMock(return_value=None)  # ← ИСПРАВЛЕНО: save вместо create
        return repo
    
    @pytest.fixture
    def mock_password_hasher(self):
        """Фикстура: стаб хешера (имитирует результат)"""
        hasher = Mock()
        hasher.hash = Mock(return_value="hashed_password_123")
        return hasher
    
    @pytest.fixture
    def register_use_case(self, mock_user_repository, mock_password_hasher):
        """Фикстура: use case с моками"""
        return RegisterUserUseCase(mock_user_repository, mock_password_hasher)
    
    # === Успешные сценарии ===
    
    @pytest.mark.asyncio
    async def test_execute_withValidData_createsUserAndReturnsUserDict(self, register_use_case):
        """Регистрация с корректными данными — создаёт пользователя и возвращает его данные"""
        # Arrange
        username = "newuser"
        email = "new@example.com"
        password = "securepass123"
        
        # Act
        result = await register_use_case.execute(username, email, password)
        
        # Assert
        assert result["username"] == username
        assert result["email"] == email
        assert "hashed_password" not in result
        assert result["role"] == "user"
        assert result["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_execute_withValidData_callsRepositorySaveOnce(self, register_use_case, mock_user_repository):
        """Регистрация с корректными данными — вызывает метод save репозитория ровно один раз"""
        # Arrange
        username = "newuser"
        email = "new@example.com"
        password = "securepass123"
        
        # Act
        await register_use_case.execute(username, email, password)
        
        # Assert
        mock_user_repository.save.assert_called_once()  # ← ИСПРАВЛЕНО: save вместо create
    
    # === Сценарии с ошибками валидации ===
    
    @pytest.mark.asyncio
    async def test_execute_withUsernameTooShort_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с именем короче 3 символов — вызывает ошибку валидации"""
        # Arrange
        username = "ab"  # 2 символа
        email = "test@example.com"
        password = "securepass123"
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await register_use_case.execute(username, email, password)
        
        assert "at least 3 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withEmptyUsername_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с пустым именем — вызывает ошибку валидации"""
        # Arrange
        username = ""
        email = "test@example.com"
        password = "securepass123"
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await register_use_case.execute(username, email, password)
    
    @pytest.mark.asyncio
    async def test_execute_withInvalidEmailFormat_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с неверным форматом email — вызывает ошибку валидации"""
        # Arrange
        username = "newuser"
        email = "not-an-email"
        password = "securepass123"
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await register_use_case.execute(username, email, password)
        
        assert "Invalid email format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withEmptyEmail_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с пустым email — вызывает ошибку валидации"""
        # Arrange
        username = "newuser"
        email = ""
        password = "securepass123"
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await register_use_case.execute(username, email, password)
    
    @pytest.mark.asyncio
    async def test_execute_withPasswordShorterThan6Chars_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с паролем короче 6 символов — вызывает ошибку валидации"""
        # Arrange
        username = "newuser"
        email = "test@example.com"
        password = "12345"  # 5 символов
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await register_use_case.execute(username, email, password)
        
        assert "at least 6 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withEmptyPassword_raisesInvalidCredentialsError(self, register_use_case):
        """Регистрация с пустым паролем — вызывает ошибку валидации"""
        # Arrange
        username = "newuser"
        email = "test@example.com"
        password = ""
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await register_use_case.execute(username, email, password)
    
    # === Сценарии с бизнес-ошибками ===
    
    @pytest.mark.asyncio
    async def test_execute_withExistingUsername_raisesUserAlreadyExistsError(self, mock_user_repository, register_use_case):
        """Регистрация с уже существующим именем — вызывает ошибку дубликата"""
        # Arrange
        mock_user_repository.exists_by_username = AsyncMock(return_value=True)
        username = "existing"
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await register_use_case.execute(username, "new@example.com", "securepass123")
        
        assert "already taken" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withExistingEmail_raisesUserAlreadyExistsError(self, mock_user_repository, register_use_case):
        """Регистрация с уже зарегистрированным email — вызывает ошибку дубликата"""
        # Arrange
        mock_user_repository.exists_by_email = AsyncMock(return_value=True)
        email = "existing@example.com"
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await register_use_case.execute("newuser", email, "securepass123")
        
        assert "already registered" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_whenRepositorySaveFails_propagatesException(self, mock_user_repository, register_use_case):
        """Регистрация при ошибке репозитория — пробрасывает исключение"""
        # Arrange
        mock_user_repository.save = AsyncMock(side_effect=Exception("DB error"))
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await register_use_case.execute("newuser", "new@example.com", "securepass123")
        
        assert "DB error" in str(exc_info.value)