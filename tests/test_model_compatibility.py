"""Тест совместимости фиктивной модели"""

import pytest
import torch
from PIL import Image
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from app.models.wagon_model import WagonClassifier
from app.config import settings


def test_dummy_model_compatibility():
    """Проверяет, что фиктивная модель совместима с загрузчиком"""
    try:
        classifier = WagonClassifier(
            model_path=settings.MODEL_PATH, class_names=settings.CLASS_NAMES
        )

        # Создаем тестовое изображение
        test_image = Image.new("RGB", (224, 224), color="red")

        # Делаем предсказание
        result = classifier.predict(test_image)

        # Проверяем результат
        assert isinstance(result, tuple)
        assert len(result) == 3
        predicted_class, confidence, probabilities = result

        assert predicted_class in settings.CLASS_NAMES
        assert 0 <= confidence <= 1
        assert isinstance(probabilities, dict)
        assert set(probabilities.keys()) == set(settings.CLASS_NAMES)

        print(
            f"✅ Dummy model works! Predicted: {predicted_class} with confidence {confidence:.2%}"
        )

    except Exception as e:
        pytest.fail(f"Model compatibility test failed: {e}")
