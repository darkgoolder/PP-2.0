"""Тест совместимости фиктивной модели"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ИСПРАВЛЕННЫЙ ИМПОРТ
from app.infrastructure.model_repository import WagonClassifier
from app.config import settings


def test_dummy_model_compatibility():
    """Проверяет, что фиктивная модель совместима с загрузчиком"""
    
    # Сначала создаем фиктивную модель, если её нет
    if not settings.MODEL_PATH.exists():
        try:
            # Создаем фиктивную модель
            import torch
            import torch.nn as nn
            from torchvision import models
            
            os.makedirs(settings.MODEL_PATH.parent, exist_ok=True)
            
            model = models.efficientnet_b2(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(in_features, len(settings.CLASS_NAMES))
            )
            
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_names": settings.CLASS_NAMES,
            }, settings.MODEL_PATH)
            
            print(f"✅ Created dummy model at {settings.MODEL_PATH}")
        except Exception as e:
            pytest.skip(f"Cannot create dummy model: {e}")
    
    try:
        from PIL import Image
        
        classifier = WagonClassifier(
            model_path=str(settings.MODEL_PATH),
            class_names=settings.CLASS_NAMES
        )

        # Создаем тестовое изображение
        test_image = Image.new("RGB", (224, 224), color="red")

        # Делаем предсказание
        predicted_class, confidence, probabilities = classifier.predict(test_image)

        # Проверяем результат
        assert predicted_class in settings.CLASS_NAMES
        assert 0 <= confidence <= 1
        assert isinstance(probabilities, dict)
        assert set(probabilities.keys()) == set(settings.CLASS_NAMES)

        print(f"✅ Dummy model works! Predicted: {predicted_class} with confidence {confidence:.2%}")

    except Exception as e:
        pytest.fail(f"Model compatibility test failed: {e}")


# Добавляем импорт os для создания фиктивной модели
import os