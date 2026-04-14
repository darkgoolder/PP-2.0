"""
Unit-тесты для use case входа пользователя
Соблюдение правил:
- Моки для внешних зависимостей
- AAA (Arrange-Act-Assert)
- Один тест - один сценарий
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.use_cases.login_user import LoginUserUseCase
from app.domain.entities import User, UserRole
from app.domain.exceptions import InvalidCredentialsError, UserNotActiveError


class TestLoginUserUseCase:
    """
    Тесты use case входа пользователя
    Имя класса соответствует тестируемой сущности
    """
    
    @pytest.fixture
    def mock_user_repository(self):
        """Фикстура: стаб репозитория"""
        repo = Mock()
        repo.find_by_username = AsyncMock()
        repo.update_last_login = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_password_hasher(self):
        """Фикстура: стаб хешера паролей"""
        hasher = Mock()
        hasher.verify = Mock(return_value=True)
        return hasher
    
    @pytest.fixture
    def active_user(self):
        """Фикстура: активный пользователь"""
        return User(
            id="123",
            username="activeuser",
            email="active@example.com",
            hashed_password="hashed_correct",
            role=UserRole.USER,
            is_active=True
        )
    
    @pytest.fixture
    def inactive_user(self):
        """Фикстура: неактивный пользователь"""
        return User(
            id="456",
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="hashed_correct",
            role=UserRole.USER,
            is_active=False
        )
    
    @pytest.fixture
    def login_use_case(self, mock_user_repository, mock_password_hasher):
        """Фикстура: use case с моками"""
        return LoginUserUseCase(mock_user_repository, mock_password_hasher)
    
    # === Успешные сценарии ===
    
    @pytest.mark.asyncio
    async def test_execute_withValidCredentials_returnsUserDict(self, login_use_case, mock_user_repository, mock_password_hasher, active_user):
        """Вход с корректными данными — возвращает данные пользователя"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=active_user)
        mock_password_hasher.verify = Mock(return_value=True)
        username = "activeuser"
        password = "correctpassword"
        
        # Act
        result = await login_use_case.execute(username, password)
        
        # Assert
        assert result["id"] == "123"
        assert result["username"] == "activeuser"
        assert result["email"] == "active@example.com"
        assert "hashed_password" not in result
    
    @pytest.mark.asyncio
    async def test_execute_withValidCredentials_updatesLastLogin(self, login_use_case, mock_user_repository, mock_password_hasher, active_user):
        """Вход с корректными данными — обновляет время последнего входа"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=active_user)
        mock_password_hasher.verify = Mock(return_value=True)
        username = "activeuser"
        password = "correctpassword"
        
        # Act
        await login_use_case.execute(username, password)
        
        # Assert
        mock_user_repository.update_last_login.assert_called_once_with(username)
    
    # === Сценарии с ошибками ===
    
    @pytest.mark.asyncio
    async def test_execute_withNonexistentUser_raisesInvalidCredentialsError(self, login_use_case, mock_user_repository):
        """Вход с несуществующим пользователем — вызывает ошибку авторизации"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await login_use_case.execute("nonexistent", "anypass")
        
        assert "Invalid username or password" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withWrongPassword_raisesInvalidCredentialsError(self, login_use_case, mock_user_repository, mock_password_hasher, active_user):
        """Вход с неверным паролем — вызывает ошибку авторизации"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=active_user)
        mock_password_hasher.verify = Mock(return_value=False)
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await login_use_case.execute("activeuser", "wrongpassword")
        
        assert "Invalid username or password" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_withInactiveUser_raisesUserNotActiveError(self, login_use_case, mock_user_repository, mock_password_hasher, inactive_user):
        """Вход неактивного пользователя — вызывает ошибку деактивации"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=inactive_user)
        mock_password_hasher.verify = Mock(return_value=True)
        
        # Act & Assert
        with pytest.raises(UserNotActiveError) as exc_info:
            await login_use_case.execute("inactiveuser", "correctpassword")
        
        assert "deactivated" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_whenRepositoryFindsUserButHasherThrows_propagatesException(self, login_use_case, mock_user_repository, active_user):
        """Вход при ошибке хешера — пробрасывает исключение"""
        # Arrange
        mock_user_repository.find_by_username = AsyncMock(return_value=active_user)
        
        class BrokenHasher:
            def verify(self, password, hashed):
                raise Exception("Hasher failed")
        
        broken_hasher = BrokenHasher()
        broken_use_case = LoginUserUseCase(mock_user_repository, broken_hasher)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await broken_use_case.execute("activeuser", "anypass")
        
        assert "Hasher failed" in str(exc_info.value)