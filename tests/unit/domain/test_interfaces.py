"""
Тесты для покрытия interfaces.py
"""

import pytest
from app.domain.interfaces import (
    IImageClassifier,
    IUserRepository,
    IPasswordHasher
)


class TestInterfacesCoverage:
    """Тесты интерфейсов для покрытия"""
    
    def test_iimage_classifier_has_required_methods(self):
        """IImageClassifier — имеет все требуемые методы"""
        assert hasattr(IImageClassifier, "predict")
        assert hasattr(IImageClassifier, "predict_batch")
        assert hasattr(IImageClassifier, "device")
        assert hasattr(IImageClassifier, "class_names")
        assert hasattr(IImageClassifier, "class_names_ru")
    
    def test_iuser_repository_has_required_methods(self):
        """IUserRepository — имеет все требуемые методы"""
        assert hasattr(IUserRepository, "save")
        assert hasattr(IUserRepository, "find_by_username")
        assert hasattr(IUserRepository, "find_by_email")
        assert hasattr(IUserRepository, "exists_by_username")
        assert hasattr(IUserRepository, "exists_by_email")
        assert hasattr(IUserRepository, "update_last_login")
        assert hasattr(IUserRepository, "get_all")
    
    def test_ipassword_hasher_has_required_methods(self):
        """IPasswordHasher — имеет все требуемые методы"""
        assert hasattr(IPasswordHasher, "hash")
        assert hasattr(IPasswordHasher, "verify")