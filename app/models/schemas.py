"""
Pydantic схемы для валидации данных API
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime


class PredictionResponse(BaseModel):
    """Ответ API с предсказанием"""
    status: str = Field(..., example="success")
    data: Dict = Field(..., description="Результат классификации")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Уникальный идентификатор запроса")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "class": "pered",
                    "class_name": "передняя часть вагона",
                    "confidence": 0.95,
                    "probabilities": {
                        "pered": 0.95,
                        "zad": 0.03,
                        "none": 0.02
                    }
                },
                "timestamp": "2024-01-15T10:30:00",
                "request_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ErrorResponse(BaseModel):
    """Ответ при ошибке"""
    status: str = Field(..., example="error")
    error: Dict = Field(..., description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": {
                    "code": "INVALID_IMAGE",
                    "message": "Файл не является корректным изображением",
                    "details": "Поддерживаются форматы: jpg, jpeg, png"
                },
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class HealthResponse(BaseModel):
    """Проверка здоровья сервиса"""
    status: str = Field(..., description="Статус сервиса")
    model_loaded: bool = Field(..., description="Загружена ли модель")
    device: str = Field(..., description="Устройство выполнения")
    version: str = Field(..., description="Версия API")


class BatchPredictionResponse(BaseModel):
    """Ответ для пакетной классификации"""
    status: str = Field(..., example="success")
    results: List[Dict] = Field(..., description="Результаты для каждого файла")
    total: int = Field(..., description="Всего файлов")
    successful: int = Field(..., description="Успешно обработано")