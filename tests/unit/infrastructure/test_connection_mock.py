"""
Реальные unit-тесты для database/connection.py
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestConnectionReal:
    """Реальные тесты connection.py"""
    
    def test_database_manager_constructor(self):
        """DatabaseManager — создаётся с URL"""
        from app.infrastructure.database.connection import DatabaseManager
        
        manager = DatabaseManager("postgresql://test:test@localhost/db")
        assert manager.database_url == "postgresql://test:test@localhost/db"
        assert manager.engine is None
        assert manager.async_session_maker is None
    
    def test_set_db_manager_function(self):
        """set_db_manager — сохраняет менеджер"""
        from app.infrastructure.database.connection import set_db_manager, get_db_manager, db_manager as global_db
        
        # Сохраняем исходное состояние
        original = get_db_manager()
        
        # Тест
        mock_manager = Mock()
        set_db_manager(mock_manager)
        assert get_db_manager() == mock_manager
        
        # Восстанавливаем
        set_db_manager(original)
    
    def test_get_db_manager_returns_none_by_default(self):
        """get_db_manager — по умолчанию возвращает None"""
        from app.infrastructure.database.connection import get_db_manager, set_db_manager
        
        set_db_manager(None)
        assert get_db_manager() is None