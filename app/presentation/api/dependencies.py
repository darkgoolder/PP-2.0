# """
# Зависимости для API маршрутов
# """

# from fastapi import HTTPException, status
# from app.infrastructure.model_repository import get_classifier


# async def verify_model_loaded():
#     """Проверка, что модель загружена"""
#     try:
#         classifier = get_classifier()
#         if classifier.model is None:
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 detail="Модель не загружена",
#             )
#         return classifier
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=f"Ошибка загрузки модели: {str(e)}",
#         )


"""
DI контейнер для API
"""

from app.infrastructure.model_repository import get_classifier
from app.use_cases.predict_side import PredictSideUseCase


def get_predict_use_case() -> PredictSideUseCase:
    """Получение use case для предсказания"""
    classifier = get_classifier()
    return PredictSideUseCase(classifier)