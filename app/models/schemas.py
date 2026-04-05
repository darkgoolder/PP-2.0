"""
Pydantic схемы для валидации данных API
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime


class PredictionResponse(BaseModel):
    """Ответ API с предсказанием"""

    status: str = Field(..., example="success")
    data: Dict[str, Any] = Field(..., description="Результат классификации")
    request_id: Optional[str] = Field(
        None, description="Уникальный идентификатор запроса"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "class": "pered",
                    "class_name": "передняя часть вагона",
                    "confidence": 0.95,
                    "probabilities": {"pered": 0.95, "zad": 0.03, "none": 0.02},
                },
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-15T10:30:00",
            }
        }


class ErrorResponse(BaseModel):
    """Ответ при ошибке"""

    status: str = Field(..., example="error")
    error: Dict[str, Any] = Field(..., description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": {
                    "code": "INVALID_IMAGE",
                    "message": "Файл не является корректным изображением",
                    "details": "Поддерживаются форматы: jpg, jpeg, png",
                },
                "timestamp": "2024-01-15T10:30:00",
            }
        }


class HealthResponse(BaseModel):
    """Проверка здоровья сервиса"""

    status: str = Field(..., description="Статус сервиса", example="healthy")
    model_loaded: bool = Field(..., description="Загружена ли модель", example=True)
    device: str = Field(..., description="Устройство выполнения", example="cuda")
    version: str = Field(..., description="Версия API", example="2.0.0")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "device": "cuda",
                "version": "2.0.0"
            }
        }


class BatchPredictionResponse(BaseModel):
    """Ответ для пакетной классификации"""

    status: str = Field(..., example="success")
    results: List[Dict[str, Any]] = Field(..., description="Результаты для каждого файла")
    total: int = Field(..., description="Всего файлов")
    successful: int = Field(..., description="Успешно обработано")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "results": [
                    {
                        "filename": "wagon1.jpg",
                        "success": True,
                        "result": {
                            "class": "pered",
                            "class_name": "передняя часть вагона",
                            "confidence": 0.95,
                            "probabilities": {"pered": 0.95, "zad": 0.03, "none": 0.02}
                        }
                    }
                ],
                "total": 1,
                "successful": 1
            }
        }