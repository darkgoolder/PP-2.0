"""
Unit-тесты для PostgresUserRepository (с моками, без реальной БД)
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from app.infrastructure.database.postgres_user_repository import PostgresUserRepository
from app.domain.entities import User, UserRole


class TestPostgresUserRepositoryMock:
    """Тесты репозитория с моками (без реальной БД)"""
    
    @pytest.fixture
    def mock_session(self):
        """Мок асинхронной сессии SQLAlchemy"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return PostgresUserRepository(mock_session)
    
    @pytest.fixture
    def sample_user(self):
        return User(
            id="123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123",
            role=UserRole.USER
        )
    
    @pytest.mark.asyncio
    async def test_save_calls_session_add_and_flush(self, repository, mock_session, sample_user):
        """Метод save — вызывает session.add и session.flush"""
        # Act
        await repository.save(sample_user)
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_username_calls_execute(self, repository, mock_session):
        """Метод find_by_username — вызывает session.execute"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        await repository.find_by_username("testuser")
        
        # Assert
        mock_session.execute.assert_called_once()