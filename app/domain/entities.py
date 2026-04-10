"""
Сущности предметной области
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class WagonSide(str, Enum):
    """Сторона вагона"""
    PERED = "pered"      # Передняя часть
    ZAD = "zad"          # Задняя часть
    NONE = "none"        # Вагон не обнаружен


@dataclass
class PredictionResult:
    """Результат предсказания (Value Object)"""
    side: WagonSide
    confidence: float
    probabilities: Dict[str, float]
    image_filename: str
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None
    
    @property
    def class_name_ru(self) -> str:
        """Русское название класса"""
        names = {
            WagonSide.PERED: "передняя часть вагона",
            WagonSide.ZAD: "задняя часть вагона",
            WagonSide.NONE: "вагон не обнаружен"
        }
        return names.get(self.side, self.side.value)
    
    def to_dict(self) -> Dict:
        """Преобразование в словарь для API ответа"""
        return {
            "class": self.side.value,
            "class_name": self.class_name_ru,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
        }