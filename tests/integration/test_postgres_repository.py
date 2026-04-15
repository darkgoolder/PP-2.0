"""
Интеграционные тесты для PostgreSQL репозитория
Соблюдение правил:
- AAA (Arrange-Act-Assert)
- Один тест - одна проверка
- Говорящие имена
- Изоляция тестов (каждый тест в своей транзакции)
"""

"""
Интеграционные тесты для PostgreSQL (синхронные)
"""

import pytest
import uuid
from datetime import datetime


class TestPostgresUserRepository:
    """Тесты PostgreSQL репозитория пользователей"""
    
    def test_insert_user_successfully(self, db_cursor):
        """Вставка пользователя — данные сохраняются в БД"""
        # Arrange
        user_id = str(uuid.uuid4())
        username = "testuser"
        email = "test@example.com"
        hashed_password = "hashed123"
        
        # Act
        db_cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, email, hashed_password))
        
        # Assert
        db_cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = db_cursor.fetchone()
        assert result is not None
        assert result[1] == username
        assert result[2] == email
    
    def test_find_user_by_username(self, db_cursor):
        """Поиск пользователя по имени — возвращает правильные данные"""
        # Arrange
        user_id = str(uuid.uuid4())
        username = "finduser"
        email = "find@example.com"
        
        db_cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, email, "hash123"))
        
        # Act
        db_cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = db_cursor.fetchone()
        
        # Assert
        assert result is not None
        assert result[1] == username
        assert result[2] == email
    
    def test_find_user_by_username_not_exists(self, db_cursor):
        """Поиск несуществующего пользователя — возвращает None"""
        # Act
        db_cursor.execute("SELECT * FROM users WHERE username = %s", ("nonexistent",))
        result = db_cursor.fetchone()
        
        # Assert
        assert result is None
    
    def test_check_username_exists(self, db_cursor):
        """Проверка существования имени — возвращает True для существующего"""
        # Arrange
        user_id = str(uuid.uuid4())
        username = "existsuser"
        
        db_cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, "exists@test.com", "hash"))
        
        # Act
        db_cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s)", (username,))
        exists = db_cursor.fetchone()[0]
        
        # Assert
        assert exists is True
    
    def test_check_username_not_exists(self, db_cursor):
        """Проверка существования имени — возвращает False для несуществующего"""
        # Act
        db_cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s)", ("nosuchuser",))
        exists = db_cursor.fetchone()[0]
        
        # Assert
        assert exists is False
    
    def test_duplicate_username_error(self, db_cursor):
        """Вставка дублирующегося имени — вызывает ошибку"""
        # Arrange
        user_id1 = str(uuid.uuid4())
        user_id2 = str(uuid.uuid4())
        
        db_cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password)
            VALUES (%s, %s, %s, %s)
        """, (user_id1, "duplicate", "first@test.com", "hash1"))
        
        # Act & Assert
        from psycopg2 import IntegrityError
        with pytest.raises(IntegrityError):
            db_cursor.execute("""
                INSERT INTO users (id, username, email, hashed_password)
                VALUES (%s, %s, %s, %s)
            """, (user_id2, "duplicate", "second@test.com", "hash2"))
    
    def test_update_last_login(self, db_cursor):
        """Обновление времени последнего входа — timestamp обновляется"""
        # Arrange
        user_id = str(uuid.uuid4())
        username = "loginuser"
        
        db_cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, "login@test.com", "hash"))
        
        # Act
        db_cursor.execute("""
            UPDATE users SET last_login = NOW() WHERE username = %s
        """, (username,))
        
        # Assert
        db_cursor.execute("SELECT last_login FROM users WHERE username = %s", (username,))
        last_login = db_cursor.fetchone()[0]
        assert last_login is not None