"""
Фикстуры для интеграционных тестов (синхронная версия)
"""

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(scope="session")
def db_connection():
    """Создание тестовой БД и подключение"""
    
    # Подключение к postgres для создания тестовой БД
    conn_admin = psycopg2.connect(
        host="localhost",
        port=5432,
        user="wagon_user",
        password="wagon_pass",
        database="postgres"
    )
    conn_admin.autocommit = True
    cursor = conn_admin.cursor()
    
    # Удалить тестовую БД если существует
    cursor.execute("DROP DATABASE IF EXISTS wagon_db_test")
    
    # Создать тестовую БД
    cursor.execute("CREATE DATABASE wagon_db_test")
    
    cursor.close()
    conn_admin.close()
    
    # Подключение к тестовой БД
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="wagon_user",
        password="wagon_pass",
        database="wagon_db_test"
    )
    
    # Создание таблиц
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE
        )
    """)
    conn.commit()
    cursor.close()
    
    yield conn
    
    # Очистка после тестов
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    cursor.close()
    conn.close()
    
    # Удалить тестовую БД
    conn_admin = psycopg2.connect(
        host="localhost",
        port=5432,
        user="wagon_user",
        password="wagon_pass",
        database="postgres"
    )
    conn_admin.autocommit = True
    cursor = conn_admin.cursor()
    cursor.execute("DROP DATABASE IF EXISTS wagon_db_test")
    cursor.close()
    conn_admin.close()


@pytest.fixture
def db_cursor(db_connection):
    """Фикстура курсора с откатом после каждого теста"""
    cursor = db_connection.cursor()
    yield cursor
    db_connection.rollback()
    cursor.close()