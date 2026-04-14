"""
Unit-тесты для репозитория модели (с моками)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from app.infrastructure.model_repository import WagonClassifier


class TestWagonClassifier:
    """Тесты классификатора с моками"""
    
    @pytest.fixture
    def mock_model(self):
        """Мок модели PyTorch"""
        model = MagicMock()
        model.return_value = MagicMock()
        return model
    
    @pytest.fixture
    def classifier(self, tmp_path):
        """Создание классификатора с временным файлом модели"""
        import torch
        import torch.nn as nn
        from torchvision import models
        
        # Создаём фиктивную модель
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_classifier_initialization(self, classifier):
        """Классификатор инициализируется корректно"""
        assert classifier is not None
        assert classifier.device == 'cpu'
        assert len(classifier.class_names) == 3
    
    def test_predict_returns_tuple(self, classifier):
        """Метод predict возвращает кортеж из 3 элементов"""
        image = Image.new('RGB', (224, 224), color='red')
        
        result = classifier.predict(image)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], str)  # class
        assert isinstance(result[1], float)  # confidence
        assert isinstance(result[2], dict)  # probabilities
        
    def test_predict_batch_returns_list(self, classifier):
        """Пакетное предсказание — возвращает список результатов"""
        # Arrange - создаём ДВА изображения
        images = [
            Image.new('RGB', (224, 224), color='red'),
            Image.new('RGB', (224, 224), color='blue')
        ]
        
        # Act
        results = classifier.predict_batch(images)
        
        # Assert
        assert isinstance(results, list)
        assert len(results) == 2  # теперь будет 2
        for result in results:
            assert "class" in result
            assert "confidence" in result
            assert "probabilities" in result
            
            
class TestWagonClassifierProperties:
    """Тесты свойств классификатора"""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        from app.infrastructure.model_repository import WagonClassifier
        import torch
        import torch.nn as nn
        from torchvision import models
        
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_class_names_property(self, classifier):
        """Свойство class_names — возвращает список классов"""
        assert classifier.class_names == ['pered', 'zad', 'none']
    
    def test_device_property(self, classifier):
        """Свойство device — возвращает устройство"""
        assert classifier.device in ['cuda', 'cpu']
    
    def test_class_names_ru_property(self, classifier):
        """Свойство class_names_ru — возвращает русские названия"""
        assert "pered" in classifier.class_names_ru
        assert "zad" in classifier.class_names_ru
        assert "none" in classifier.class_names_ru