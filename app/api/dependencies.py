"""
Зависимости для API маршрутов
"""

from fastapi import Request, HTTPException, status
from app.models.wagon_model import get_classifier


async def verify_model_loaded():
    """Проверка, что модель загружена"""
    try:
        classifier = get_classifier()
        if classifier.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Модель не загружена"
            )
        return classifier
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ошибка загрузки модели: {str(e)}"
        )