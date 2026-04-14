"""
Сущности предметной области
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
import uuid

class WagonSide(str, Enum):
    """Сторона вагона"""

    PERED = "pered"  # Передняя часть
    ZAD = "zad"  # Задняя часть
    NONE = "none"  # Вагон не обнаружен


@dataclass
class PredictionResult:
    """Результат предсказания (Value Object)"""
    side: WagonSide
    confidence: float
    probabilities: Dict[str, float]
    image_filename: str
    user_id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def class_name_ru(self) -> str:
        """Русское название класса"""
        names = {
            WagonSide.PERED: "передняя часть вагона",
            WagonSide.ZAD: "задняя часть вагона",
            WagonSide.NONE: "вагон не обнаружен",
        }
        return names.get(self.side, self.side.value)

    def to_dict(self) -> Dict:
        return {
            "class": self.side.value,
            "class_name": self.class_name_ru,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """Сущность пользователя"""

    id: str
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime = None

    def verify_password(self, password: str, hasher) -> bool:
        return hasher.verify(password, self.hashed_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
    def activate(self):
        """Активация пользователя"""
        self.is_active = True

    def deactivate(self):
        """Деактивация пользователя"""
        self.is_active = False
