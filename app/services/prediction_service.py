"""
Сервис для работы с предсказаниями
Содержит бизнес-логику обработки изображений
"""

import logging
from typing import Dict, Any, List
from PIL import Image

from app.models.wagon_model import WagonClassifier

logger = logging.getLogger(__name__)


class PredictionService:
    """Сервис для выполнения предсказаний"""
    
    def __init__(self, classifier: WagonClassifier):
        self.classifier = classifier
    
    def predict_single(self, image: Image.Image) -> Dict[str, Any]:
        """
        Предсказание для одного изображения
        
        Args:
            image: PIL Image
            
        Returns:
            Словарь с результатами предсказания
        """
        predicted_class, confidence, probabilities = self.classifier.predict(image)
        
        return {
            "class": predicted_class,
            "class_name": self.classifier.class_names_ru.get(predicted_class, predicted_class),
            "confidence": confidence,
            "probabilities": probabilities
        }
    
    def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """
        Предсказание для нескольких изображений
        
        Args:
            images: Список PIL Image
            
        Returns:
            Список результатов
        """
        results = []
        for image in images:
            try:
                result = self.predict_single(image)
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при предсказании: {e}")
                results.append({"error": str(e)})
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получить информацию о модели"""
        return {
            "device": self.classifier.device,
            "classes": self.classifier.class_names,
            "num_classes": self.classifier.num_classes
        }