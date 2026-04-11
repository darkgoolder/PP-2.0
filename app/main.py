# """
# Основной файл приложения FastAPI
# """

# from app.infrastructure.metrics import MetricsMiddleware, get_metrics
# from app.config import settings
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# import logging
# import os
# from pathlib import Path

# from app.presentation.api.routes import router
# from app.config import settings
# from app.infrastructure.logger import setup_logging 

# # Настройка логирования
# setup_logging(settings.LOG_LEVEL)
# logger = logging.getLogger(__name__)

# # Создаем приложение
# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     version=settings.VERSION,
#     description="API для классификации вагонов по изображениям\n\n"
#                 "Определяет переднюю и заднюю часть вагона на фотографии.",
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_tags=[
#         {
#             "name": "System",
#             "description": "Системные эндпоинты (health check)"
#         },
#         {
#             "name": "Prediction",
#             "description": "Эндпоинты для классификации изображений"
#         }
#     ]
# )

# # Добавляем middleware для сбора метрик
# app.add_middleware(MetricsMiddleware)

# # Добавляем эндпоинт для метрик Prometheus
# app.add_api_route("/metrics", get_metrics, methods=["GET"], include_in_schema=False)

# # Настройка CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Подключаем API роуты
# app.include_router(router, prefix=settings.API_V1_PREFIX)

# # Статические файлы (веб-интерфейс)
# static_dir = Path(__file__).parent / "static"
# if static_dir.exists():
#     app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# @app.get("/")
# async def root():
#     """Главная страница"""
#     static_index = static_dir / "index.html"
#     if static_index.exists():
#         return FileResponse(str(static_index))
#     return {
#         "message": settings.PROJECT_NAME,
#         "version": settings.VERSION,
#         "docs": "/docs",
#         "health": f"{settings.API_V1_PREFIX}/health"
#     }


# @app.on_event("startup")
# async def startup_event():
#     """Загрузка модели при старте"""
#     logger.info("=" * 50)
#     logger.info(f"Запуск {settings.PROJECT_NAME} v{settings.VERSION}")
#     logger.info("=" * 50)

#     # Проверяем существование модели
#     if not os.path.exists(settings.MODEL_PATH):
#         logger.warning(f"⚠️ Модель не найдена: {settings.MODEL_PATH}")
#         logger.info("Пожалуйста, обучите модель командой: python train_model.py")
#     else:
#         try:
#             # Предварительная загрузка модели
#             from app.models.wagon_model import get_classifier
#             classifier = get_classifier()
#             logger.info(f"✅ Модель загружена на устройство: {classifier.device}")
#             logger.info(f"📋 Доступные классы: {classifier.class_names}")
#         except Exception as e:
#             logger.error(f"❌ Ошибка при загрузке модели: {e}")


# @app.on_event("shutdown")
# async def shutdown_event():
#     """Очистка при завершении"""
#     logger.info("Остановка API сервиса")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True
#     )




"""
Основной файл приложения FastAPI
"""

from app.infrastructure.database.connection import DatabaseManager, set_db_manager
from app.infrastructure.metrics import MetricsMiddleware, get_metrics
from app.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from pathlib import Path

from app.presentation.api.routes import router
from app.infrastructure.logger import setup_logging 

# Настройка логирования
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API для классификации вагонов по изображениям",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Добавляем middleware для сбора метрик
app.add_middleware(MetricsMiddleware)

# Добавляем эндпоинт для метрик Prometheus
app.add_api_route("/metrics", get_metrics, methods=["GET"], include_in_schema=False)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(router, prefix=settings.API_V1_PREFIX)

# Статические файлы (веб-интерфейс)
static_dir = Path(__file__).parent / "presentation" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Главная страница"""
    static_index = static_dir / "index.html"
    if static_index.exists():
        return FileResponse(str(static_index))
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


@app.on_event("startup")
async def startup_event():
    """Загрузка модели и инициализация БД при старте"""
    logger.info("=" * 50)
    logger.info(f"Запуск {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("=" * 50)

    # ============================================
    # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (ДОБАВЛЕНО)
    # ============================================
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            db_manager = DatabaseManager(database_url)
            await db_manager.initialize()
            set_db_manager(db_manager)
            logger.info("✅ PostgreSQL database connected")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL not available: {e}")
            logger.info("ℹ️ Continuing without database (user registration disabled)")
    else:
        logger.info("ℹ️ DATABASE_URL not set, running without database")

    # ============================================
    # ЗАГРУЗКА МОДЕЛИ (СУЩЕСТВУЮЩИЙ КОД)
    # ============================================
    if not os.path.exists(settings.MODEL_PATH):
        logger.warning(f"⚠️ Модель не найдена: {settings.MODEL_PATH}")
        logger.info("Обучите модель: python -m app.presentation.cli.train_cli --data-dir /path/to/data")
    else:
        try:
            from app.infrastructure.model_repository import get_classifier
            classifier = get_classifier()
            logger.info(f"✅ Модель загружена на устройство: {classifier.device}")
            logger.info(f"📋 Доступные классы: {classifier.class_names}")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке модели: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Остановка сервиса"""
    # Закрываем соединение с БД
    from app.infrastructure.database.connection import get_db_manager
    db_manager = get_db_manager()
    if db_manager:
        await db_manager.close()
        logger.info("Database connection closed")
    
    logger.info("Остановка API сервиса")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )