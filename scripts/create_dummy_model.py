"""Создание фиктивной модели для CI/CD тестов (совместимой с EfficientNet-B2)"""

import torch
import torch.nn as nn
from torchvision import models
import os
import sys


def create_dummy_model():
    """Создает корректную фиктивную модель для тестов"""
    os.makedirs("models", exist_ok=True)

    # Определяем устройство
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Создаем модель с ТОЧНО такой же архитектурой, как в train_model.py
    model = models.efficientnet_b2(weights=None)  # Без предобученных весов

    # Заменяем классификатор на 3 класса (как в вашей модели)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3), nn.Linear(in_features, 3)  # 3 класса: pered, zad, none
    )

    # Инициализируем веса случайно (но корректно)
    def init_weights(m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)

    model.apply(init_weights)
    model = model.to(device)

    # Сохраняем в формате, который ожидает ваш WagonClassifier
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "class_names": ["pered", "zad", "none"],
        "epoch": 0,
        "val_acc": 0.5,
        "train_acc": 0.5,
    }

    torch.save(checkpoint, "models/best_model.pth")

    # Проверяем что файл создан корректно
    if os.path.exists("models/best_model.pth"):
        file_size = os.path.getsize("models/best_model.pth")
        print("✅ Dummy model created at models/best_model.pth")
        print(f"📦 Model file size: {file_size} bytes")

        # Проверяем, что модель можно загрузить
        try:
            test_checkpoint = torch.load("models/best_model.pth", map_location="cpu")
            assert "model_state_dict" in test_checkpoint
            print("✅ Model checkpoint is valid")
        except Exception as e:
            print(f"❌ Model checkpoint is invalid: {e}")
            sys.exit(1)
    else:
        print("❌ Failed to create model")
        sys.exit(1)


if __name__ == "__main__":
    create_dummy_model()
