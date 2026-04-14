"""
Unit-тесты для хешера паролей
"""

import pytest
from app.infrastructure.password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasher:
    """Тесты хешера паролей bcrypt"""
    
    @pytest.fixture
    def hasher(self):
        """Фикстура хешера"""
        return BcryptPasswordHasher()
    
    def test_hash_validPassword_returnsDifferentString(self, hasher):
        """Хеширование пароля — возвращает строку, отличную от исходной"""
        # Arrange
        password = "mySecretPassword123"
        
        # Act
        hashed = hasher.hash(password)
        
        # Assert
        assert hashed != password
        assert len(hashed) > 20
    
    def test_hash_samePasswordTwice_returnsDifferentHashes(self, hasher):
        """Хеширование одного пароля дважды — возвращает разные хеши (из-за соли)"""
        # Arrange
        password = "samePassword"
        
        # Act
        hashed1 = hasher.hash(password)
        hashed2 = hasher.hash(password)
        
        # Assert
        assert hashed1 != hashed2
    
    def test_hash_emptyString_returnsValidHash(self, hasher):
        """Хеширование пустой строки — возвращает корректный хеш"""
        # Act
        hashed = hasher.hash("")
        
        # Assert
        assert hashed is not None
        assert len(hashed) > 0
    
    def test_verify_correctPassword_returnsTrue(self, hasher):
        """Проверка корректного пароля — возвращает True"""
        # Arrange
        password = "correctPassword123"
        hashed = hasher.hash(password)
        
        # Act
        result = hasher.verify(password, hashed)
        
        # Assert
        assert result is True
    
    def test_verify_wrongPassword_returnsFalse(self, hasher):
        """Проверка неверного пароля — возвращает False"""
        # Arrange
        password = "correctPassword123"
        wrong_password = "wrongPassword123"
        hashed = hasher.hash(password)
        
        # Act
        result = hasher.verify(wrong_password, hashed)
        
        # Assert
        assert result is False
    
    def test_verify_emptyPasswordWithNonEmptyHash_returnsFalse(self, hasher):
        """Проверка пустого пароля с существующим хешем — возвращает False"""
        # Arrange
        password = "realPassword123"
        hashed = hasher.hash(password)
        
        # Act
        result = hasher.verify("", hashed)
        
        # Assert
        assert result is False