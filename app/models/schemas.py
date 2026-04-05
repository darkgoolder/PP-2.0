"""
Pydantic схемы для валидации данных API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, Any
from datetime import datetime


class PredictionResponse(BaseModel):
    """Ответ API с предсказанием"""
    
    status: str = Field(default=..., description="Статус ответа")
    data: Dict[str, Any] = Field(default=..., description="Результат классификации")
    request_id: Optional[str] = Field(default=None, description="Уникальный идентификатор запроса")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        json_schema_extra={
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
    )


class ErrorResponse(BaseModel):
    """Ответ при ошибке"""
    
    status: str = Field(default=..., description="Статус ответа")
    error: Dict[str, Any] = Field(default=..., description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        json_schema_extra={
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
    )


class HealthResponse(BaseModel):
    """Проверка здоровья сервиса"""
    
    status: str = Field(default=..., description="Статус сервиса")
    model_loaded: bool = Field(default=..., description="Загружена ли модель")
    device: str = Field(default=..., description="Устройство выполнения")
    version: str = Field(default=..., description="Версия API")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "device": "cuda",
                "version": "2.0.0",
            }
        }
    )


class BatchPredictionResponse(BaseModel):
    """Ответ для пакетной классификации"""
    
    status: str = Field(default=..., description="Статус ответа")
    results: List[Dict[str, Any]] = Field(default=..., description="Результаты для каждого файла")
    total: int = Field(default=..., description="Всего файлов")
    successful: int = Field(default=..., description="Успешно обработано")
    
    model_config = ConfigDict(
        json_schema_extra={
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
                            "probabilities": {"pered": 0.95, "zad": 0.03, "none": 0.02},
                        },
                    }
                ],
                "total": 1,
                "successful": 1,
            }
        }
    )