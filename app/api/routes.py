"""
API эндпоинты для классификации вагонов
"""

import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from PIL import Image
import io

from app.models.schemas import PredictionResponse, ErrorResponse, HealthResponse, BatchPredictionResponse
from app.models.wagon_model import get_classifier
from app.config import settings
from app.utils.image_utils import validate_image_file, process_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Проверка здоровья сервиса"
)
async def health_check():
    """
    Проверка работоспособности API и наличия модели
    """
    try:
        classifier = get_classifier()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            device=classifier.device,
            version=settings.VERSION
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            device="unknown",
            version=settings.VERSION
        )


@router.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Классификация одного изображения",
    responses={
        400: {"model": ErrorResponse, "description": "Ошибка валидации"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"}
    }
)
async def predict_image(
    file: UploadFile = File(..., description="Изображение вагона")
):
    """
    Классифицирует изображение вагона
    
    Определяет:
    - **pered** - передняя часть вагона
    - **zad** - задняя часть вагона  
    - **none** - вагон не обнаружен
    
    Возвращает предсказанный класс и уверенность модели.
    """
    try:
        # Валидация файла
        validate_image_file(file, settings)
        
        # Загружаем изображение
        image = process_image(file)
        
        # Получаем модель и делаем предсказание
        classifier = get_classifier()
        predicted_class, confidence, probabilities = classifier.predict(image)
        
        # Формируем ответ
        response_data = {
            "class": predicted_class,
            "class_name": classifier.class_names_ru.get(predicted_class, predicted_class),
            "confidence": confidence,
            "probabilities": probabilities
        }
        
        return PredictionResponse(
            status="success",
            data=response_data,
            request_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервера"
            }
        )


@router.post(
    "/predict-batch",
    tags=["Prediction"],
    summary="Пакетная классификация изображений"
)
async def predict_batch(
    files: List[UploadFile] = File(..., description="Список изображений")
):
    """
    Классифицирует несколько изображений одновременно
    
    Максимальное количество файлов не ограничено, но каждый файл
    должен соответствовать требованиям по размеру и формату.
    """
    try:
        classifier = get_classifier()
        results = []
        
        for file in files:
            try:
                # Валидация
                validate_image_file(file, settings)
                image = process_image(file)
                
                # Предсказание
                predicted_class, confidence, probabilities = classifier.predict(image)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "result": {
                        "class": predicted_class,
                        "class_name": classifier.class_names_ru.get(predicted_class, predicted_class),
                        "confidence": confidence,
                        "probabilities": probabilities
                    }
                })
                
            except HTTPException as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": e.detail.get("message", str(e.detail))
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "results": results,
                "total": len(results),
                "successful": sum(1 for r in results if r["success"])
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка пакетной обработки: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BATCH_ERROR",
                "message": "Ошибка пакетной обработки"
            }
        )