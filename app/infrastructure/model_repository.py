"""
Обертка для модели машинного обучения
Загружает обученную модель и выполняет предсказания
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset
from torchvision import models, transforms

from app.infrastructure.metrics import record_prediction_metrics

logger = logging.getLogger(__name__)


# ================================================
# ДАТАСЕТ (из train_model_legacy.py)
# ================================================


def load_image_safe(image_path, target_size=(224, 224)):
    """Безопасная загрузка изображения с обработкой ошибок"""
    try:
        image = Image.open(image_path)
        image.verify()
        image = Image.open(image_path)

        if image.mode != "RGB":
            image = image.convert("RGB")

        if image.size[0] == 0 or image.size[1] == 0:
            image = Image.new("RGB", target_size, color="black")

        return image
    except Exception as e:
        logger.warning(f"Ошибка загрузки {image_path}: {e}")
        return Image.new("RGB", target_size, color="black")


class RobustWagonDataset(Dataset):
    """Надежный датасет с обработкой поврежденных изображений"""

    def __init__(self, data_dir, class_names, transform=None, mode="train"):
        self.image_paths = []
        self.labels = []
        self.transform = transform

        data_path = os.path.join(data_dir, mode)

        for class_idx, class_name in enumerate(class_names):
            class_dir = os.path.join(data_path, class_name)
            if not os.path.exists(class_dir):
                logger.warning(f"Папка {class_dir} не найдена!")
                continue

            images = [
                f
                for f in os.listdir(class_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            for img in images:
                self.image_paths.append(os.path.join(class_dir, img))
                self.labels.append(class_idx)

        logger.info(f"{mode.upper()}: загружено {len(self.image_paths)} изображений")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = load_image_safe(img_path)

        if self.transform:
            image = self.transform(image)

        return image, self.labels[idx]


def create_model(num_classes: int = 3) -> nn.Module:
    """Создание модели EfficientNet-B2"""
    model = models.efficientnet_b2(weights="DEFAULT")
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3), nn.Linear(in_features, num_classes)
    )
    return model


# ================================================
# КЛАССИФИКАТОР (существующий код)
# ================================================


class WagonClassifier:
    """Классификатор вагонов"""

    def __init__(
        self, model_path: str, class_names: List[str], device: Optional[str] = None
    ):
        self.model_path = model_path
        self.class_names = class_names
        self.num_classes = len(class_names)

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Используется устройство: {self.device}")

        self.model = self._load_model()

        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        self.class_names_ru = {
            "pered": "передняя часть вагона",
            "zad": "задняя часть вагона",
            "none": "вагон не обнаружен",
        }

        logger.info(f"Модель загружена. Классы: {self.class_names}")

    def _load_model(self) -> nn.Module:
        start_time = time.time()

        model = create_model(self.num_classes)

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        checkpoint = torch.load(self.model_path, map_location=self.device)

        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)

        if missing_keys:
            logger.warning(f"Missing keys in checkpoint: {missing_keys[:5]}...")
        if unexpected_keys:
            logger.warning(f"Unexpected keys in checkpoint: {unexpected_keys[:5]}...")

        model = model.to(self.device)
        model.eval()

        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")

        return model

    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        if image.mode != "RGB":
            image = image.convert("RGB")

        input_tensor = self.transform(image)
        input_tensor = input_tensor.unsqueeze(0).to(self.device)

        return input_tensor

    def predict(self, image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        start_time = time.time()

        try:
            input_tensor = self._preprocess_image(image)

            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                predicted_idx = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_idx].item()
                predicted_class = self.class_names[predicted_idx]

                all_probs = {
                    class_name: probabilities[0][i].item()
                    for i, class_name in enumerate(self.class_names)
                }

            duration = time.time() - start_time
            try:
                record_prediction_metrics(
                    class_name=predicted_class,
                    confidence=confidence,
                    device=self.device,
                    duration=duration,
                )
            except ImportError:
                pass

            logger.info(
                f"Предсказание: {predicted_class} с уверенностью {confidence:.2%} (время: {duration:.3f}s)"
            )

            return predicted_class, confidence, all_probs

        except Exception as e:
            logger.error(f"Ошибка при предсказании: {e}")
            raise

    def predict_batch(self, images: List[Image.Image]) -> List[Dict]:
        results = []
        for image in images:
            pred_class, confidence, probs = self.predict(image)
            results.append(
                {
                    "class": pred_class,
                    "class_name": self.class_names_ru.get(pred_class, pred_class),
                    "confidence": confidence,
                    "probabilities": probs,
                }
            )
        return results


_classifier_instance = None


def get_classifier() -> WagonClassifier:
    global _classifier_instance

    if _classifier_instance is None:
        from app.config import settings

        _classifier_instance = WagonClassifier(
            model_path=str(settings.MODEL_PATH),
            class_names=settings.CLASS_NAMES,
        )

    return _classifier_instance
