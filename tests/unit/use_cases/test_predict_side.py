"""
Unit-тесты для use case предсказания стороны вагона
"""

import pytest
from unittest.mock import Mock, AsyncMock
from PIL import Image
from app.use_cases.predict_side import PredictSideUseCase
from app.domain.entities import PredictionResult, WagonSide


class TestPredictSideUseCase:
    """Тесты use case предсказания"""
    
    @pytest.fixture
    def mock_classifier(self):
        """Мок классификатора"""
        classifier = Mock()
        classifier.predict = Mock(return_value=("pered", 0.95, {"pered": 0.95, "zad": 0.03, "none": 0.02}))
        classifier.class_names = ["pered", "zad", "none"]
        classifier.class_names_ru = {"pered": "передняя часть вагона", "zad": "задняя часть вагона", "none": "вагон не обнаружен"}
        classifier.device = "cpu"
        return classifier
    
    @pytest.fixture
    def sample_image(self):
        """Тестовое изображение"""
        return Image.new("RGB", (224, 224), color="red")
    
    @pytest.fixture
    def use_case(self, mock_classifier):
        """Use case с моком"""
        return PredictSideUseCase(mock_classifier)
    
    def test_predictSingle_validImage_returnsPredictionResult(self, use_case, sample_image):
        """Предсказание одного изображения — возвращает PredictionResult"""
        # Act
        result = use_case.predict_single(sample_image, "test.jpg")
        
        # Assert
        assert isinstance(result, PredictionResult)
        assert result.side == WagonSide.PERED
        assert result.confidence == 0.95
        assert result.image_filename == "test.jpg"
        assert result.request_id is not None
    
    def test_predictSingleDict_validImage_returnsDict(self, use_case, sample_image):
        """Предсказание одного изображения (словарь) — возвращает dict"""
        # Act
        result = use_case.predict_single_dict(sample_image)
        
        # Assert
        assert isinstance(result, dict)
        assert result["class"] == "pered"
        assert result["confidence"] == 0.95
        assert "probabilities" in result
    
    def test_predictBatch_multipleImages_returnsListOfResults(self, use_case, sample_image):
        """Пакетное предсказание — возвращает список результатов"""
        # Arrange
        images = [sample_image, sample_image]
        
        # Act
        results = use_case.predict_batch(images)
        
        # Assert
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(r, PredictionResult) for r in results)
    
    def test_getModelInfo_returnsClassifierInfo(self, use_case):
        """Получение информации о модели — возвращает словарь с данными"""
        # Act
        info = use_case.get_model_info()
        
        # Assert
        assert "device" in info
        assert "classes" in info
        assert "num_classes" in info
        assert "class_names_ru" in info
        assert info["device"] == "cpu"
        assert info["num_classes"] == 3