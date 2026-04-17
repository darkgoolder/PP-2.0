# app/main.py
"""
Основной файл приложения FastAPI
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.infrastructure.database.connection import DatabaseManager, set_db_manager
from app.infrastructure.logger import setup_logging
from app.infrastructure.metrics import MetricsMiddleware, get_metrics
from app.presentation.api.routes import router
from app.presentation.api.secrets_router import router as secrets_router

# Настройка логирования
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="API для классификации вагонов по изображениям",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Добавляем middleware для сбора метрик
app.add_middleware(MetricsMiddleware)

# Добавляем эндпоинт для метрик Prometheus
app.add_api_route("/metrics", get_metrics, methods=["GET"], include_in_schema=False)

# Настройка CORS (без ALLOWED_ORIGINS - разрешаем все для простоты)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(router, prefix=settings.api_v1_prefix)
app.include_router(secrets_router, prefix=settings.api_v1_prefix)

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
        "message": settings.project_name,
        "version": settings.version,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }


@app.on_event("startup")
async def startup_event():
    """Загрузка модели и инициализация БД при старте"""
    logger.info("=" * 50)
    logger.info(f"Запуск {settings.project_name} v{settings.version}")
    logger.info("=" * 50)

    # ============================================
    # ИНИЦИАЛИЗАЦИЯ S3 И СЕКРЕТОВ
    # ============================================
    logger.info("🔄 Инициализация S3 хранилища...")
    try:
        from app.infrastructure import s3_storage
        await s3_storage.list_objects(settings.secrets_bucket)
        logger.info(f"✅ S3 подключен: {settings.minio_endpoint}")
        logger.info(f"📦 Бакет секретов: {settings.secrets_bucket}")
    except Exception as e:
        logger.warning(f"⚠️ S3 недоступен: {e}")

    # ============================================
    # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
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
    else:
        logger.info("ℹ️ DATABASE_URL not set, running without database")

    # ============================================
    # ЗАГРУЗКА МОДЕЛИ
    # ============================================
    if not os.path.exists(settings.model_path):
        logger.warning(f"⚠️ Модель не найдена: {settings.model_path}")
    else:
        try:
            from app.infrastructure.model_repository import get_classifier
            classifier = get_classifier()
            logger.info(f"✅ Модель загружена на устройство: {classifier.device}")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке модели: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Остановка сервиса"""
    from app.infrastructure.database.connection import get_db_manager
    db_manager = get_db_manager()
    if db_manager:
        await db_manager.close()
        logger.info("Database connection closed")
    logger.info("Остановка API сервиса")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)