"""
API эндпоинты для классификации вагонов и пользователей
"""

import logging
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.infrastructure.database.connection import get_db_manager
from app.infrastructure.database.postgres_user_repository import PostgresUserRepository
from app.infrastructure.image_processor import process_image, validate_image_file
from app.infrastructure.model_repository import get_classifier
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.presentation.schemas import (
    HealthResponse,
    LoginRequest,
    LoginResponse,
    PredictionResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.use_cases.login_user import LoginUserUseCase
from app.use_cases.register_user import RegisterUserUseCase

logger = logging.getLogger(__name__)
router = APIRouter()

from datetime import datetime

from app.infrastructure.database.models import PredictionLogModel

# ================================================
# Эндпоинты для проверки здоровья
# ================================================


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        classifier = get_classifier()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            device=classifier.device,
            version=settings.version,
        )
    except Exception:
        return HealthResponse(
            status="healthy",
            model_loaded=False,
            device="cpu",
            version=settings.version,
        )


# ================================================
# Эндпоинты для предсказаний
# ================================================


@router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_image(file: UploadFile = File(..., description="Изображение вагона")):
    """Классифицирует изображение вагона"""
    try:
        validate_image_file(file, settings)
        image = process_image(file)

        classifier = get_classifier()
        predicted_class, confidence, probabilities = classifier.predict(image)

        # ===== Логирование предсказания =====
        db_manager = get_db_manager()
        if db_manager:
            async for session in db_manager.get_session():
                try:
                    log = PredictionLogModel(
                        image_filename=file.filename,
                        predicted_class=predicted_class,
                        confidence=confidence,
                        created_at=datetime.now(),
                        request_id=str(uuid.uuid4()),
                    )
                    session.add(log)
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Failed to log prediction: {e}")
                break
        # ============================================

        response_data = {
            "class": predicted_class,
            "class_name": classifier.class_names_ru.get(
                predicted_class, predicted_class
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
            detail={"code": "MODEL_NOT_FOUND", "message": "Модель не загружена"},
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(e)},
        )


@router.post("/predict-batch", tags=["Prediction"])
async def predict_batch(
    files: List[UploadFile] = File(..., description="Список изображений")
):
    """Пакетная классификация изображений"""
    try:
        classifier = get_classifier()
        results = []

        for file in files:
            try:
                validate_image_file(file, settings)
                image = process_image(file)
                predicted_class, confidence, probabilities = classifier.predict(image)

                results.append(
                    {
                        "filename": file.filename,
                        "success": True,
                        "result": {
                            "class": predicted_class,
                            "class_name": classifier.class_names_ru.get(
                                predicted_class, predicted_class
                            ),
                            "confidence": confidence,
                            "probabilities": probabilities,
                        },
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
            detail={"code": "BATCH_ERROR", "message": str(e)},
        )


# @router.post("/register", response_model=RegisterResponse, tags=["Users"])
# async def register_user(request: RegisterRequest):
#     """Регистрация нового пользователя - УПРОЩЁННАЯ ВЕРСИЯ ДЛЯ ТЕСТА"""

#     db_manager = get_db_manager()
#     if not db_manager:
#         raise HTTPException(status_code=503, detail="Database not available")

#     session = None
#     try:
#         async for sess in db_manager.get_session():
#             session = sess
#             break

#         print("=== SESSION ACQUIRED ===")

#         import uuid
#         from datetime import datetime

#         from app.infrastructure.database.models import UserModel

#         new_user = UserModel(
#             id=str(uuid.uuid4()),
#             username=request.username,
#             email=request.email,
#             hashed_password="test_hash",
#             created_at=datetime.now(),
#         )

#         session.add(new_user)
#         print(f"=== ADDED TO SESSION: {new_user.username} ===")

#         await session.flush()
#         print("=== FLUSH DONE ===")

#         # ЯВНЫЙ КОММИТ
#         await session.commit()
#         print("=== COMMIT DONE ===")

#         return RegisterResponse(
#             status="success",
#             user={
#                 "id": str(new_user.id),
#                 "username": new_user.username,
#                 "email": new_user.email,
#                 "role": "user",
#                 "is_active": True,
#                 "created_at": new_user.created_at.isoformat(),
#                 "last_login": None,
#             },
#             message="User registered successfully",
#         )
#     except Exception as e:
#         if session:
#             await session.rollback()
#         print(f"ERROR: {e}")
#         raise HTTPException(status_code=400, detail=str(e))


@router.post("/register", response_model=RegisterResponse, tags=["Users"])
async def register_user(request: RegisterRequest):
    """Регистрация нового пользователя"""
    db_manager = get_db_manager()
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_manager.async_session_maker() as session:
            async with session.begin():
                user_repository = PostgresUserRepository(session)
                password_hasher = BcryptPasswordHasher()
                use_case = RegisterUserUseCase(user_repository, password_hasher)

                user = await use_case.execute(
                    username=request.username,
                    email=request.email,
                    password=request.password,
                )

                return RegisterResponse(
                    status="success", user=user, message="User registered successfully"
                )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=400, detail={"code": "REGISTRATION_ERROR", "message": str(e)}
        )


@router.post("/login", response_model=LoginResponse, tags=["Users"])
async def login_user(request: LoginRequest):
    """Аутентификация пользователя"""
    db_manager = get_db_manager()
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_manager.async_session_maker() as session:
            async with session.begin():
                user_repository = PostgresUserRepository(session)
                password_hasher = BcryptPasswordHasher()
                use_case = LoginUserUseCase(user_repository, password_hasher)

                user = await use_case.execute(
                    username=request.username, password=request.password
                )

                return LoginResponse(status="success", user=user)
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=401, detail={"code": "LOGIN_ERROR", "message": str(e)}
        )


@router.get("/users", tags=["Users"])
async def get_all_users():
    """Получить всех пользователей"""
    db_manager = get_db_manager()
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async for session in db_manager.get_session():
            user_repository = PostgresUserRepository(session)
            users = await user_repository.get_all()
            return {"status": "success", "users": [u.to_dict() for u in users]}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail={"message": str(e)})
