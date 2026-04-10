# """
# API эндпоинты для классификации вагонов
# """

# import uuid
# import logging
# from typing import List
# from fastapi import APIRouter, File, UploadFile, HTTPException, status
# from fastapi.responses import JSONResponse

# from app.presentation.schemas import PredictionResponse, ErrorResponse, HealthResponse
# from app.infrastructure.model_repository import get_classifier
# from app.infrastructure.image_processor import process_image, validate_image_file
# from app.config import settings

# logger = logging.getLogger(__name__)
# router = APIRouter()


# @router.get(
#     "/health",
#     response_model=HealthResponse,
#     tags=["System"],
#     summary="Проверка здоровья сервиса",
# )
# async def health_check():
#     """
#     Проверка работоспособности API и наличия модели
#     """
#     try:
#         classifier = get_classifier()
#         return HealthResponse(
#             status="healthy",
#             model_loaded=True,
#             device=classifier.device,
#             version=settings.VERSION,
#         )
#     except Exception as e:
#         logger.error(f"Health check failed: {e}")
#         # Возвращаем healthy даже если модели нет, но с model_loaded=False
#         return HealthResponse(
#             status="healthy",  # Изменено: всегда healthy для API
#             model_loaded=False,
#             device="cpu",
#             version=settings.VERSION,
#         )


# @router.post(
#     "/predict",
#     response_model=PredictionResponse,
#     tags=["Prediction"],
#     summary="Классификация одного изображения",
#     responses={
#         400: {"model": ErrorResponse, "description": "Ошибка валидации"},
#         413: {"model": ErrorResponse, "description": "Файл слишком большой"},
#         500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"},
#     },
# )
# async def predict_image(file: UploadFile = File(..., description="Изображение вагона")):
#     """
#     Классифицирует изображение вагона

#     Определяет:
#     - **pered** - передняя часть вагона
#     - **zad** - задняя часть вагона
#     - **none** - вагон не обнаружен

#     Возвращает предсказанный класс и уверенность модели.
#     """
#     try:
#         # Валидация файла
#         validate_image_file(file, settings)

#         # Загружаем изображение
#         image = process_image(file)

#         # Получаем модель и делаем предсказание
#         classifier = get_classifier()

#         # Проверяем, что метод predict возвращает кортеж из 3 элементов
#         result = classifier.predict(image)

#         # Обрабатываем разные форматы возврата
#         if isinstance(result, tuple) and len(result) == 3:
#             predicted_class, confidence, probabilities = result
#         elif isinstance(result, dict):
#             predicted_class = result.get("class")
#             confidence = result.get("confidence")
#             probabilities = result.get("probabilities")
#         else:
#             raise ValueError("Unexpected predict return format")

#         # Формируем ответ
#         response_data = {
#             "class": predicted_class,
#             "class_name": (
#                 classifier.class_names_ru.get(predicted_class, predicted_class)
#                 if hasattr(classifier, "class_names_ru")
#                 else predicted_class
#             ),
#             "confidence": confidence,
#             "probabilities": probabilities,
#         }

#         return PredictionResponse(
#             status="success", data=response_data, request_id=str(uuid.uuid4())
#         )

#     except HTTPException:
#         raise
#     except FileNotFoundError as e:
#         logger.error(f"Модель не найдена: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail={
#                 "code": "MODEL_NOT_FOUND",
#                 "message": "Модель не загружена. Сначала обучите модель.",
#             },
#         )
#     except Exception as e:
#         logger.error(f"Непредвиденная ошибка: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={
#                 "code": "INTERNAL_ERROR",
#                 "message": f"Внутренняя ошибка сервера: {str(e)}",
#             },
#         )


# @router.post(
#     "/predict-batch", tags=["Prediction"], summary="Пакетная классификация изображений"
# )
# async def predict_batch(
#     files: List[UploadFile] = File(..., description="Список изображений")
# ):
#     """
#     Классифицирует несколько изображений одновременно

#     Максимальное количество файлов не ограничено, но каждый файл
#     должен соответствовать требованиям по размеру и формату.
#     """
#     try:
#         classifier = get_classifier()
#         results = []

#         for file in files:
#             try:
#                 # Валидация
#                 validate_image_file(file, settings)
#                 image = process_image(file)

#                 # Предсказание
#                 result = classifier.predict(image)

#                 if isinstance(result, tuple) and len(result) == 3:
#                     predicted_class, confidence, probabilities = result
#                 elif isinstance(result, dict):
#                     predicted_class = result.get("class")
#                     confidence = result.get("confidence")
#                     probabilities = result.get("probabilities")
#                 else:
#                     raise ValueError("Unexpected predict return format")

#                 results.append(
#                     {
#                         "filename": file.filename,
#                         "success": True,
#                         "result": {
#                             "class": predicted_class,
#                             "class_name": (
#                                 classifier.class_names_ru.get(
#                                     predicted_class, predicted_class
#                                 )
#                                 if hasattr(classifier, "class_names_ru")
#                                 else predicted_class
#                             ),
#                             "confidence": confidence,
#                             "probabilities": probabilities,
#                         },
#                     }
#                 )

#             except HTTPException as e:
#                 error_detail = e.detail
#                 if isinstance(error_detail, dict):
#                     error_message = error_detail.get("message", str(e.detail))
#                 else:
#                     error_message = str(e.detail)

#                 results.append(
#                     {
#                         "filename": file.filename,
#                         "success": False,
#                         "error": error_message,
#                     }
#                 )
#             except Exception as e:
#                 results.append(
#                     {"filename": file.filename, "success": False, "error": str(e)}
#                 )

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "status": "success",
#                 "results": results,
#                 "total": len(results),
#                 "successful": sum(1 for r in results if r["success"]),
#             },
#         )

#     except Exception as e:
#         logger.error(f"Ошибка пакетной обработки: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={
#                 "code": "BATCH_ERROR",
#                 "message": f"Ошибка пакетной обработки: {str(e)}",
#             },
#         )





"""
API эндпоинты для классификации вагонов и пользователей
"""

import uuid
import logging
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from app.presentation.schemas import PredictionResponse, ErrorResponse, HealthResponse
from app.infrastructure.image_processor import process_image, validate_image_file
from app.config import settings

# Импорты для пользователей
from app.presentation.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.use_cases.register_user import RegisterUserUseCase
from app.use_cases.login_user import LoginUserUseCase
from app.infrastructure.user_repository import JsonUserRepository
from app.infrastructure.password_hasher import BcryptPasswordHasher

logger = logging.getLogger(__name__)
router = APIRouter()


# ================================================
# Эндпоинты для проверки здоровья
# ================================================

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        from app.infrastructure.model_repository import get_classifier
        classifier = get_classifier()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            device=classifier.device,
            version=settings.VERSION,
        )
    except Exception:
        return HealthResponse(
            status="healthy",
            model_loaded=False,
            device="cpu",
            version=settings.VERSION,
        )


# ================================================
# Эндпоинты для предсказаний
# ================================================

@router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_image(
    file: UploadFile = File(..., description="Изображение вагона")
):
    """Классифицирует изображение вагона"""
    try:
        validate_image_file(file, settings)
        image = process_image(file)
        
        from app.infrastructure.model_repository import get_classifier
        classifier = get_classifier()
        
        predicted_class, confidence, probabilities = classifier.predict(image)
        
        response_data = {
            "class": predicted_class,
            "class_name": classifier.class_names_ru.get(predicted_class, predicted_class),
            "confidence": confidence,
            "probabilities": probabilities,
        }
        
        return PredictionResponse(
            status="success",
            data=response_data,
            request_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Модель не найдена: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "MODEL_NOT_FOUND", "message": "Модель не загружена"}
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.post("/predict-batch", tags=["Prediction"])
async def predict_batch(
    files: List[UploadFile] = File(..., description="Список изображений")
):
    """Пакетная классификация изображений"""
    try:
        from app.infrastructure.model_repository import get_classifier
        classifier = get_classifier()
        results = []
        
        for file in files:
            try:
                validate_image_file(file, settings)
                image = process_image(file)
                predicted_class, confidence, probabilities = classifier.predict(image)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "result": {
                        "class": predicted_class,
                        "class_name": classifier.class_names_ru.get(predicted_class, predicted_class),
                        "confidence": confidence,
                        "probabilities": probabilities,
                    }
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
                "successful": sum(1 for r in results if r["success"]),
            }
        )
    except Exception as e:
        logger.error(f"Ошибка пакетной обработки: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "BATCH_ERROR", "message": str(e)}
        )


# ================================================
# Эндпоинты для пользователей
# ================================================

@router.post("/register", response_model=RegisterResponse, tags=["Users"])
async def register_user(request: RegisterRequest):
    """Регистрация нового пользователя"""
    try:
        user_repository = JsonUserRepository("users.json")
        password_hasher = BcryptPasswordHasher()
        
        use_case = RegisterUserUseCase(user_repository, password_hasher)
        user = await use_case.execute(
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        return RegisterResponse(
            status="success",
            user=user,
            message="User registered successfully"
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REGISTRATION_ERROR", "message": str(e)}
        )


@router.post("/login", response_model=LoginResponse, tags=["Users"])
async def login_user(request: LoginRequest):
    """Аутентификация пользователя"""
    try:
        user_repository = JsonUserRepository("users.json")
        password_hasher = BcryptPasswordHasher()
        
        use_case = LoginUserUseCase(user_repository, password_hasher)
        user = await use_case.execute(
            username=request.username,
            password=request.password
        )
        
        return LoginResponse(
            status="success",
            user=user
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "LOGIN_ERROR", "message": str(e)}
        )


@router.get("/users", tags=["Users"])
async def get_all_users():
    """Получить всех пользователей (админский эндпоинт)"""
    try:
        user_repository = JsonUserRepository("users.json")
        users = await user_repository.get_all()
        return {"status": "success", "users": [u.to_dict() for u in users]}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)}
        )