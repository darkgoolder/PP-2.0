"""Тест совместимости фиктивной модели"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.model_repository import WagonClassifier
from app.config import settings


def test_dummy_model_compatibility():
    """Проверяет, что фиктивная модель совместима с загрузчиком"""
    
    # 🔧 ИСПРАВЛЕНО: Используем Path объект
    model_path = Path(settings.model_path)
    
    # Создаем фиктивную модель, если её нет
    if not model_path.exists():
        try:
            import torch
            import torch.nn as nn
            from torchvision import models
            
            # Создаем директорию если её нет
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Получаем количество классов
            class_names = settings.CLASS_NAMES
            if isinstance(class_names, str):
                class_list = [c.strip() for c in class_names.split(",")]
                num_classes = len(class_list)
            else:
                num_classes = len(class_names)
            
            # Создаем dummy модель
            model = models.efficientnet_b2(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(in_features, num_classes)
            )
            
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_names": class_names,
            }, model_path)
            
            print(f"✅ Created dummy model at {model_path}")
        except Exception as e:
            pytest.skip(f"Cannot create dummy model: {e}")
    
    try:
        from PIL import Image
        
        classifier = WagonClassifier(
            model_path=str(model_path),  # Передаем как строку для совместимости
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