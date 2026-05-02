#!/usr/bin/env python
"""
Скрипт для создания фиктивной модели для тестов
"""

import torch
import torch.nn as nn
from torchvision import models
import os
from pathlib import Path


def create_dummy_model():
    """Создание фиктивной модели для тестов"""
    
    # Создаем директорию models если её нет
    Path("models").mkdir(parents=True, exist_ok=True)
    
    # Создаем модель
    model = models.efficientnet_b2(weights=None)
    num_classes = 3
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes)
    )
    
    # ИСПРАВЛЕНО: Сохраняем class_names как строку для совместимости с настройками
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': 'pered,zad,none'  # ← строка, а не список
    }, 'models/dummy_model.pth')
    
    print('✅ Dummy model created as models/dummy_model.pth')
    print(f'   Model classes: pered, zad, none')
    print(f'   File size: {os.path.getsize("models/dummy_model.pth")} bytes')


if __name__ == "__main__":
    create_dummy_model()