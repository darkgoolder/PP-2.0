"""
Сущности предметной области
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


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

@dataclass
class DailyReport:
    """Сущность для ежедневного отчёта (Value Object)"""

    report_date: datetime
    new_users_count: int
    total_predictions: int
    model_exists: bool
    model_accuracy: Optional[float] = None
    report_generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "report_date": self.report_date.isoformat(),
            "new_users_count": self.new_users_count,
            "total_predictions": self.total_predictions,
            "model_exists": self.model_exists,
            "model_accuracy": self.model_accuracy,
            "report_generated_at": self.report_generated_at.isoformat(),
        }
        
# ============================================
# НОВЫЕ СУЩНОСТИ ДЛЯ СЕКРЕТОВ
# ============================================

@dataclass
class Secret:
    """Сущность секрета для хранения в S3"""
    key: str
    value: str
    encrypted: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
    
    def update(self, new_value: str):
        """Обновление значения секрета"""
        self.value = new_value
        self.updated_at = datetime.now()
    
    def mask_value(self) -> str:
        """Маскирование значения для вывода (безопасно)"""
        if len(self.value) > 8:
            return self.value[:4] + "***" + self.value[-4:]
        return "***"
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.mask_value(),
            "encrypted": self.encrypted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SecretsBatch:
    """Пакет секретов (Aggregate Root)"""
    secrets: Dict[str, str]
    version: str = "1.0"
    environment: str = "development"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
    
    def add_secret(self, key: str, value: str):
        """Добавление секрета"""
        self.secrets[key] = value
        self.updated_at = datetime.now()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Получение секрета"""
        return self.secrets.get(key)
    
    def remove_secret(self, key: str) -> bool:
        """Удаление секрета"""
        if key in self.secrets:
            del self.secrets[key]
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_keys(self) -> list:
        """Список ключей секретов"""
        return list(self.secrets.keys())
    
    def count(self) -> int:
        """Количество секретов"""
        return len(self.secrets)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "environment": self.environment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "secrets": self.secrets
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SecretsBatch":
        return cls(
            secrets=data.get("secrets", {}),
            version=data.get("version", "1.0"),
            environment=data.get("environment", "development"),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now())
        )


@dataclass
class SecretBackup:
    """Сущность бэкапа секретов"""
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    secret_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "secret_count": self.secret_count,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2)
        }