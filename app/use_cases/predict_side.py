# """
# Сервис для работы с предсказаниями
# Содержит бизнес-логику обработки изображений
# """

# import logging
# from typing import Dict, Any, List
# from PIL import Image

# from app.models.wagon_model import WagonClassifier

# logger = logging.getLogger(__name__)


# class PredictionService:
#     """Сервис для выполнения предсказаний"""

#     def __init__(self, classifier: WagonClassifier):
#         self.classifier = classifier

#     def predict_single(self, image: Image.Image) -> Dict[str, Any]:
#         """
#         Предсказание для одного изображения

#         Args:
#             image: PIL Image

#         Returns:
#             Словарь с результатами предсказания
#         """
#         predicted_class, confidence, probabilities = self.classifier.predict(image)

#         return {
#             "class": predicted_class,
#             "class_name": self.classifier.class_names_ru.get(
#                 predicted_class, predicted_class
#             ),
#             "confidence": confidence,
#             "probabilities": probabilities,
#         }

#     def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
#         """
#         Предсказание для нескольких изображений

#         Args:
#             images: Список PIL Image

#         Returns:
#             Список результатов
#         """
#         results = []
#         for image in images:
#             try:
#                 result = self.predict_single(image)
#                 results.append(result)
#             except Exception as e:
#                 logger.error(f"Ошибка при предсказании: {e}")
#                 results.append({"error": str(e)})

#         return results

#     def get_model_info(self) -> Dict[str, Any]:
#         """Получить информацию о модели"""
#         return {
#             "device": self.classifier.device,
#             "classes": self.classifier.class_names,
#             "num_classes": self.classifier.num_classes,
#         }


"""
Use Case: Предсказание стороны вагона
Содержит бизнес-логику обработки изображений
"""

import logging
from typing import Any, Dict, List

from PIL import Image

from app.domain.entities import PredictionResult, WagonSide
from app.domain.interfaces import IImageClassifier

logger = logging.getLogger(__name__)


class PredictSideUseCase:
    """Use case для выполнения предсказаний"""

    def __init__(self, classifier: IImageClassifier):
        self.classifier = classifier

    def predict_single(
        self, image: Image.Image, filename: str = "unknown"
    ) -> PredictionResult:
        """
        Предсказание для одного изображения

        Args:
            image: PIL Image
            filename: Имя файла

        Returns:
            PredictionResult: Результат предсказания
        """
        predicted_class, confidence, probabilities = self.classifier.predict(image)

        return PredictionResult(
            side=WagonSide(predicted_class),
            confidence=confidence,
            probabilities=probabilities,
            image_filename=filename,
        )

    def predict_single_dict(self, image: Image.Image) -> Dict[str, Any]:
        """
        Предсказание для одного изображения (словарь для обратной совместимости)

        Args:
            image: PIL Image

        Returns:
            Словарь с результатами предсказания
        """
        result = self.predict_single(image)
        return result.to_dict()

    def predict_batch(self, images: List[Image.Image]) -> List[PredictionResult]:
        """
        Предсказание для нескольких изображений

        Args:
            images: Список PIL Image

        Returns:
            Список результатов
        """
        results = []
        for idx, image in enumerate(images):
            try:
                result = self.predict_single(image, f"image_{idx}")
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при предсказании: {e}")
                # Создаем результат с ошибкой
                error_result = PredictionResult(
                    side=WagonSide.NONE,
                    confidence=0.0,
                    probabilities={},
                    image_filename=f"image_{idx}",
                )
                results.append(error_result)

        return results

    def predict_batch_dict(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """
        Пакетное предсказание (словари для обратной совместимости)
        """
        results = self.predict_batch(images)
        return [r.to_dict() for r in results]

    def get_model_info(self) -> Dict[str, Any]:
        """Получить информацию о модели"""
        return {
            "device": self.classifier.device,
            "classes": self.classifier.class_names,
            "num_classes": len(self.classifier.class_names),
            "class_names_ru": self.classifier.class_names_ru,
        }
