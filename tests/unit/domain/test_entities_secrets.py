"""
Unit-тесты для сущностей секретов
"""

import pytest
from datetime import datetime
from app.domain.entities import Secret, SecretsBatch, SecretBackup


class TestSecret:
    """Тесты сущности Secret"""
    
    def test_create_secret(self):
        """Создание секрета — все поля заполнены"""
        secret = Secret(key="api_key", value="secret_value")
        
        assert secret.key == "api_key"
        assert secret.value == "secret_value"
        assert secret.encrypted is True
        assert isinstance(secret.created_at, datetime)
        assert isinstance(secret.updated_at, datetime)
    
    def test_update_changes_value_and_timestamp(self):
        """Обновление секрета — меняет значение и timestamp"""
        from datetime import datetime
        
        secret = Secret(key="key", value="old_value")
        old_updated = secret.updated_at
        
        # Небольшая задержка, чтобы timestamp изменился
        import time
        time.sleep(0.01)
        
        secret.update("new_value")
        
        assert secret.value == "new_value"
        assert secret.updated_at > old_updated
    
    def test_mask_value_hides_part_of_long_secret(self):
        """Маскирование длинного секрета — скрывает середину"""
        secret = Secret(key="key", value="1234567890123456")
        
        masked = secret.mask_value()
        
        assert masked == "1234***3456"
        assert "1234567890123456" not in masked
    
    def test_mask_value_hides_short_secret(self):
        """Маскирование короткого секрета — заменяет на ***"""
        secret = Secret(key="key", value="1234")
        
        masked = secret.mask_value()
        
        assert masked == "***"
    
    def test_to_dict_returns_masked_value(self):
        """Преобразование в словарь — возвращает замаскированное значение"""
        secret = Secret(key="api_key", value="super_secret_value_123")
        
        data = secret.to_dict()
        
        assert data["key"] == "api_key"
        # Проверяем, что значение замаскировано (не равно исходному)
        assert data["value"] != "super_secret_value_123"
        assert "super_secret_value_123" not in data["value"]
        assert data["encrypted"] is True
        # Проверяем, что маскировка работает (должна быть ***)
        assert "***" in data["value"]


class TestSecretsBatch:
    """Тесты пакета секретов"""
    
    @pytest.fixture
    def batch(self):
        return SecretsBatch(
            secrets={"key1": "value1", "key2": "value2"},
            environment="test"
        )
    
    def test_add_secret_adds_to_dict(self, batch):
        """Добавление секрета — появляется в словаре"""
        batch.add_secret("key3", "value3")
        
        assert batch.get_secret("key3") == "value3"
        assert batch.count() == 3
    
    def test_get_secret_returns_value(self, batch):
        """Получение секрета — возвращает значение"""
        value = batch.get_secret("key1")
        
        assert value == "value1"
    
    def test_get_secret_nonexistent_returns_none(self, batch):
        """Получение несуществующего секрета — возвращает None"""
        value = batch.get_secret("nonexistent")
        
        assert value is None
    
    def test_remove_secret_removes_from_dict(self, batch):
        """Удаление секрета — удаляет из словаря"""
        result = batch.remove_secret("key1")
        
        assert result is True
        assert batch.get_secret("key1") is None
        assert batch.count() == 1
    
    def test_remove_nonexistent_returns_false(self, batch):
        """Удаление несуществующего секрета — возвращает False"""
        result = batch.remove_secret("nonexistent")
        
        assert result is False
        assert batch.count() == 2
    
    def test_get_keys_returns_list_of_keys(self, batch):
        """Получение ключей — возвращает список"""
        keys = batch.get_keys()
        
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) == 2
    
    def test_to_dict_returns_all_fields(self, batch):
        """Преобразование в словарь — содержит все поля"""
        data = batch.to_dict()
        
        assert data["version"] == "1.0"
        assert data["environment"] == "test"
        assert "secrets" in data
        assert data["secrets"]["key1"] == "value1"
    
    def test_from_dict_creates_batch(self):
        """Создание из словаря — восстанавливает объект"""
        data = {
            "secrets": {"key1": "value1"},
            "version": "2.0",
            "environment": "prod",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        batch = SecretsBatch.from_dict(data)
        
        assert batch.version == "2.0"
        assert batch.environment == "prod"
        assert batch.get_secret("key1") == "value1"


class TestSecretBackup:
    """Тесты бэкапа секретов"""
    
    def test_to_dict_returns_formatted_data(self):
        """Преобразование в словарь — возвращает форматированные данные"""
        backup = SecretBackup(
            name="backup_2024_01_01",
            size_bytes=1024 * 1024 * 5,  # 5 MB
            secret_count=10
        )
        
        data = backup.to_dict()
        
        assert data["name"] == "backup_2024_01_01"
        assert data["size_mb"] == 5.0
        assert data["secret_count"] == 10
        assert "size_bytes" in data