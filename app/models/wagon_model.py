"""
Обертка для модели машинного обучения
Загружает обученную модель и выполняет предсказания
"""

from app.utils.metrics import record_prediction_metrics
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os
import logging
import time  # <-- ДОБАВЛЕНО: импорт time
from typing import Dict, Tuple, List, Optional  # Добавьте Optional сюда

logger = logging.getLogger(__name__)


class WagonClassifier:
    """
    Классификатор вагонов
    Загружает обученную модель и выполняет инференс
    """

    def __init__(self, model_path: str, class_names: List[str], device: Optional[str] = None):
        """
        Инициализация классификатора

        Args:
            model_path: Путь к файлу с весами модели (.pth)
            class_names: Список названий классов
            device: Устройство для выполнения (cuda/cpu)
        """
        self.model_path = model_path
        self.class_names = class_names
        self.num_classes = len(class_names)

        # Определяем устройство
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Используется устройство: {self.device}")

        # Загружаем модель
        self.model = self._load_model()

        # Трансформации для изображений
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        # Русские названия классов для вывода
        self.class_names_ru = {
            "pered": "передняя часть вагона",
            "zad": "задняя часть вагона",
            "none": "вагон не обнаружен",
        }

        logger.info(f"Модель загружена. Классы: {self.class_names}")

    def _load_model(self) -> nn.Module:
        """
        Загрузка модели из файла

        Returns:
            Загруженная модель в режиме evaluation
        """
        start_time = time.time()

        # Создаем архитектуру модели (должна совпадать с train_model.py)
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3), nn.Linear(in_features, self.num_classes)
        )

        # Проверяем существование файла
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Модель не найдена: {self.model_path}")

        # Загружаем веса
        checkpoint = torch.load(self.model_path, map_location=self.device)

        # Поддерживаем разные форматы сохранения
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        # Перемещаем на устройство и переводим в режим оценки
        model = model.to(self.device)
        model.eval()

        # Записываем время загрузки
        load_time = time.time() - start_time
        try:
            from app.utils.metrics import MODEL_LOADED, MODEL_LOAD_TIME

            MODEL_LOADED.set(1)
            MODEL_LOAD_TIME.set(load_time)
        except ImportError:
            pass  # Если метрики не настроены, просто пропускаем

        logger.info(f"Модель загружена за {load_time:.2f} секунд")

        return model

    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Предобработка изображения перед подачей в модель

        Args:
            image: PIL Image

        Returns:
            Тензор, готовый для инференса
        """
        # Конвертируем в RGB если нужно
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Применяем трансформации
        input_tensor = self.transform(image)
        input_tensor = input_tensor.unsqueeze(0)  # Добавляем batch dimension
        input_tensor = input_tensor.to(self.device)

        return input_tensor

    def predict(self, image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        """
        Предсказание для одного изображения

        Args:
            image: PIL Image

        Returns:
            Кортеж (класс, уверенность, словарь вероятностей)
        """
        start_time = time.time()

        try:
            # Предобработка
            input_tensor = self._preprocess_image(image)

            # Инференс
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)

                # Получаем предсказание
                predicted_idx = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_idx].item()
                predicted_class = self.class_names[int(predicted_idx)]

                # Все вероятности
                all_probs = {
                    class_name: probabilities[0][i].item()
                    for i, class_name in enumerate(self.class_names)
                }

            # Записываем метрики
            duration = time.time() - start_time
            try:
                record_prediction_metrics(
                    class_name=predicted_class,
                    confidence=confidence,
                    device=self.device,
                    duration=duration,
                )
            except ImportError:
                pass  # Если метрики не настроены, просто пропускаем

            logger.info(
                f"Предсказание: {predicted_class} с уверенностью {confidence:.2%} (время: {duration:.3f}s)"
            )

            return predicted_class, confidence, all_probs

        except Exception as e:
            logger.error(f"Ошибка при предсказании: {e}")
            raise

    def predict_batch(self, images: List[Image.Image]) -> List[Dict]:
        """
        Пакетное предсказание для нескольких изображений

        Args:
            images: Список PIL Image

        Returns:
            Список результатов для каждого изображения
        """
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


# Глобальный экземпляр модели (синглтон)
_classifier_instance = None


def get_classifier() -> WagonClassifier:
    """
    Получить экземпляр классификатора (синглтон)
    Модель загружается только один раз при первом вызове

    Returns:
        Экземпляр WagonClassifier
    """
    global _classifier_instance

    if _classifier_instance is None:
        from app.config import settings

        _classifier_instance = WagonClassifier(
            model_path=str(settings.MODEL_PATH),  # str() преобразует Path в строку
            class_names=settings.CLASS_NAMES
        )

    return _classifier_instance
