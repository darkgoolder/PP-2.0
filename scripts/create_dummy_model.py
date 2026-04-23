#!/usr/bin/env python
"""
Скрипт для создания фиктивной модели для тестов
"""

import torch
import torch.nn as nn
from torchvision import models
import os


def create_dummy_model():
    """Создание фиктивной модели для тестов"""
    model = models.efficientnet_b2(weights=None)
    num_classes = 3
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes)
    )
    
    os.makedirs("models", exist_ok=True)
    
    # Используем ДРУГОЕ имя файла, чтобы не перезаписывать реальную модель
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': ['pered', 'zad', 'none']
    }, 'models/dummy_model.pth')  # ← другое имя
    
    print('✅ Dummy model created as models/dummy_model.pth')


if __name__ == "__main__":
    create_dummy_model()