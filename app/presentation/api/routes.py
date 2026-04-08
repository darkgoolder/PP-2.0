"""
API эндпоинты для классификации вагонов
"""

import uuid
import logging
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from app.presentation.schemas import PredictionResponse, ErrorResponse, HealthResponse
from app.infrastructure.model_repository import get_classifier
from app.infrastructure.utils.image_utils import validate_image_file, process_image
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Проверка здоровья сервиса",
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
            version=settings.VERSION,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Возвращаем healthy даже если модели нет, но с model_loaded=False
        return HealthResponse(
            status="healthy",  # Изменено: всегда healthy для API
            model_loaded=False,
            device="cpu",
            version=settings.VERSION,
        )


@router.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Классификация одного изображения",
    responses={
        400: {"model": ErrorResponse, "description": "Ошибка валидации"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"},
    },
)
async def predict_image(file: UploadFile = File(..., description="Изображение вагона")):
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

        # Проверяем, что метод predict возвращает кортеж из 3 элементов
        result = classifier.predict(image)

        # Обрабатываем разные форматы возврата
        if isinstance(result, tuple) and len(result) == 3:
            predicted_class, confidence, probabilities = result
        elif isinstance(result, dict):
            predicted_class = result.get("class")
            confidence = result.get("confidence")
            probabilities = result.get("probabilities")
        else:
            raise ValueError("Unexpected predict return format")

        # Формируем ответ
        response_data = {
            "class": predicted_class,
            "class_name": (
                classifier.class_names_ru.get(predicted_class, predicted_class)
                if hasattr(classifier, "class_names_ru")
                else predicted_class
            ),
            "confidence": confidence,
            "probabilities": probabilities,
        }

        return PredictionResponse(
            status="success", data=response_data, request_id=str(uuid.uuid4())
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Модель не найдена: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "MODEL_NOT_FOUND",
                "message": "Модель не загружена. Сначала обучите модель.",
            },
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Внутренняя ошибка сервера: {str(e)}",
            },
        )


@router.post(
    "/predict-batch", tags=["Prediction"], summary="Пакетная классификация изображений"
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
                result = classifier.predict(image)

                if isinstance(result, tuple) and len(result) == 3:
                    predicted_class, confidence, probabilities = result
                elif isinstance(result, dict):
                    predicted_class = result.get("class")
                    confidence = result.get("confidence")
                    probabilities = result.get("probabilities")
                else:
                    raise ValueError("Unexpected predict return format")

                results.append(
                    {
                        "filename": file.filename,
                        "success": True,
                        "result": {
                            "class": predicted_class,
                            "class_name": (
                                classifier.class_names_ru.get(
                                    predicted_class, predicted_class
                                )
                                if hasattr(classifier, "class_names_ru")
                                else predicted_class
                            ),
                            "confidence": confidence,
                            "probabilities": probabilities,
                        },
                    }
                )

            except HTTPException as e:
                error_detail = e.detail
                if isinstance(error_detail, dict):
                    error_message = error_detail.get("message", str(e.detail))
                else:
                    error_message = str(e.detail)

                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "error": error_message,
                    }
                )
            except Exception as e:
                results.append(
                    {"filename": file.filename, "success": False, "error": str(e)}
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "results": results,
                "total": len(results),
                "successful": sum(1 for r in results if r["success"]),
            },
        )

    except Exception as e:
        logger.error(f"Ошибка пакетной обработки: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BATCH_ERROR",
                "message": f"Ошибка пакетной обработки: {str(e)}",
            },
        )
