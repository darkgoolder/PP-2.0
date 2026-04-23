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
        
        
class TestPredictSideUseCaseEdgeCases:
    """Тесты краевых случаев use case предсказания"""
    
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.predict = Mock(return_value=("pered", 0.95, {"pered": 0.95, "zad": 0.03, "none": 0.02}))
        classifier.class_names = ["pered", "zad", "none"]
        classifier.class_names_ru = {"pered": "передняя часть вагона", "zad": "задняя часть вагона", "none": "вагон не обнаружен"}
        classifier.device = "cpu"
        return classifier
    
    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (224, 224), color="red")
    
    @pytest.fixture
    def use_case(self, mock_classifier):
        return PredictSideUseCase(mock_classifier)
    
    def test_predict_batch_handles_exception_gracefully(self, use_case, sample_image):
        """Пакетное предсказание — при ошибке одного изображения возвращает результат с None"""
        # Мокаем, что второе предсказание падает
        original_predict = use_case.classifier.predict
        call_count = 0
        
        def mock_predict(image):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Prediction failed")
            return original_predict(image)
        
        use_case.classifier.predict = mock_predict
        images = [sample_image, sample_image]
        
        results = use_case.predict_batch(images)
        
        assert len(results) == 2
        # Первый результат нормальный
        assert results[0].side == WagonSide.PERED
        # Второй результат — fallback (NONE с 0 confidence)
        assert results[1].side == WagonSide.NONE
        assert results[1].confidence == 0.0
    
    def test_predict_batch_dict_returns_dict_list(self, use_case, sample_image):
        """Пакетное предсказание в формате словаря — возвращает список словарей"""
        images = [sample_image, sample_image]
        
        results = use_case.predict_batch_dict(images)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert isinstance(results[0], dict)
        assert "class" in results[0]
        assert "confidence" in results[0]
    
    def test_predict_single_without_filename_uses_default(self, use_case, sample_image):
        """Предсказание без указания имени файла — использует 'unknown'"""
        result = use_case.predict_single(sample_image)
        
        assert result.image_filename == "unknown"
    
    def test_get_model_info_returns_complete_info(self, use_case):
        """Получение информации о модели — возвращает все поля"""
        info = use_case.get_model_info()
        
        assert "device" in info
        assert "classes" in info
        assert "num_classes" in info
        assert "class_names_ru" in info
        assert info["num_classes"] == 3
        assert info["device"] == "cpu"