"""
Абстрактные интерфейсы (порты)
Определяют контракты для внешних зависимостей
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List
from PIL import Image


class IImageClassifier(ABC):
    """Интерфейс классификатора изображений"""
    
    @abstractmethod
    def predict(self, image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        """
        Предсказание для одного изображения
        
        Returns:
            Tuple: (predicted_class, confidence, probabilities)
        """
        pass
    
    @abstractmethod
    def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Пакетное предсказание"""
        pass
    
    @property
    @abstractmethod
    def device(self) -> str:
        """Устройство выполнения"""
        pass
    
    @property
    @abstractmethod
    def class_names(self) -> List[str]:
        """Список классов"""
        pass
    
    @property
    @abstractmethod
    def class_names_ru(self) -> Dict[str, str]:
        """Русские названия классов"""
        pass