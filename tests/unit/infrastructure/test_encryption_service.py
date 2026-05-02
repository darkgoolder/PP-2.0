"""
Unit-тесты для сервиса шифрования Fernet
"""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet
from app.infrastructure.encryption_service import FernetEncryptionService


class TestFernetEncryptionService:
    """Тесты шифрования"""
    
    @pytest.fixture
    def temp_key_path(self, tmp_path):
        """Временный путь для ключа"""
        return tmp_path / "test_key"
    
    @pytest.fixture
    def service(self, temp_key_path):
        """Сервис с временным ключом"""
        return FernetEncryptionService(key_path=temp_key_path)
    
    def test_init_creates_key_file(self, temp_key_path):
        """Инициализация — создаёт файл ключа"""
        service = FernetEncryptionService(key_path=temp_key_path)
        assert temp_key_path.exists()
    
    def test_encrypt_returns_different_string(self, service):
        """Шифрование — возвращает строку, отличную от исходной"""
        plain_text = "my_secret_value"
        
        encrypted = service.encrypt(plain_text)
        
        assert encrypted != plain_text
        assert len(encrypted) > 0
    
    def test_decrypt_returns_original_string(self, service):
        """Дешифрование — возвращает исходную строку"""
        plain_text = "my_secret_value"
        
        encrypted = service.encrypt(plain_text)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plain_text
    
    def test_encrypt_twice_returns_different_results(self, service):
        """Шифрование одного текста дважды — возвращает разные результаты (из-за соли)"""
        plain_text = "same_text"
        
        encrypted1 = service.encrypt(plain_text)
        encrypted2 = service.encrypt(plain_text)
        
        assert encrypted1 != encrypted2
    
    def test_decrypt_wrong_key_fails(self, service):
        """Дешифрование с другим ключом — вызывает ошибку"""
        plain_text = "secret"
        encrypted = service.encrypt(plain_text)
        
        # Создаём другой сервис с другим ключом
        other_service = FernetEncryptionService(key_path=service.key_path.parent / "other_key")
        
        with pytest.raises(Exception):
            other_service.decrypt(encrypted)
    
    def test_loads_existing_key(self, temp_key_path):
        """Загрузка существующего ключа — работает"""
        # Сначала создаём ключ
        service1 = FernetEncryptionService(key_path=temp_key_path)
        encrypted = service1.encrypt("test")
        
        # Загружаем существующий ключ
        service2 = FernetEncryptionService(key_path=temp_key_path)
        decrypted = service2.decrypt(encrypted)
        
        assert decrypted == "test"