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
    
    model_path = Path(settings.model_path)
    
    # 🔧 Получаем список классов (всегда как список)
    if hasattr(settings, 'class_names_list') and settings.class_names_list:
        class_names_list = settings.class_names_list
    else:
        # Парсим строку в список
        class_names_raw = getattr(settings, 'CLASS_NAMES', "pered,zad,none")
        if isinstance(class_names_raw, str):
            class_names_list = [c.strip() for c in class_names_raw.split(",")]
        else:
            class_names_list = class_names_raw
    
    num_classes = len(class_names_list)
    print(f"📊 Classes: {class_names_list} (count: {num_classes})")
    
    # Создаем фиктивную модель, если её нет или она несовместима
    need_create_model = False
    
    if model_path.exists():
        # Проверяем существующую модель
        try:
            import torch
            checkpoint = torch.load(model_path, map_location='cpu')
            if 'model_state_dict' in checkpoint:
                # Проверяем размерность
                for key, value in checkpoint['model_state_dict'].items():
                    if 'classifier.1.weight' in key:
                        existing_classes = value.shape[0]
                        if existing_classes != num_classes:
                            print(f"⚠️ Model has {existing_classes} classes, need {num_classes}")
                            need_create_model = True
                        break
        except Exception as e:
            print(f"⚠️ Could not inspect model: {e}")
            need_create_model = True
    else:
        need_create_model = True
    
    if need_create_model:
        try:
            import torch
            import torch.nn as nn
            from torchvision import models
            
            # Создаем директорию
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Создаем модель с правильным количеством классов
            model = models.efficientnet_b2(weights=None)
            in_features = model.classifier[1].in_features
            
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.3, inplace=True),
                nn.Linear(in_features, num_classes)
            )
            
            # Сохраняем class_names как строку
            class_names_str = ','.join(class_names_list)
            
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_names": class_names_str,
            }, model_path)
            
            print(f"✅ Created dummy model at {model_path}")
            print(f"   Features: {in_features} → Classes: {num_classes}")
            
        except Exception as e:
            pytest.skip(f"Cannot create dummy model: {e}")
    
    try:
        from PIL import Image
        
        # 🔧 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Передаем СПИСОК
        classifier = WagonClassifier(
            model_path=str(model_path),
            class_names=class_names_list  # ← Список, не строка!
        )

        # Создаем тестовое изображение
        test_image = Image.new("RGB", (224, 224), color="red")

        # Делаем предсказание
        predicted_class, confidence, probabilities = classifier.predict(test_image)

        # Проверяем результат
        assert predicted_class in class_names_list
        assert 0 <= confidence <= 1
        assert isinstance(probabilities, dict)
        assert len(probabilities) == num_classes
        assert all(class_name in probabilities for class_name in class_names_list)

        print(f"✅ Model works! Predicted: {predicted_class} with confidence {confidence:.2%}")
        print(f"   Probabilities: {probabilities}")

    except Exception as e:
        pytest.fail(f"Model compatibility test failed: {e}")