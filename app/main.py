"""
Основной файл приложения FastAPI
"""

import torch  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
from app.utils.metrics import MetricsMiddleware, get_metrics
from app.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from pathlib import Path

from app.api.routes import router
from app.config import settings
from app.utils.logger import setup_logging

# Настройка логирования
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API для классификации вагонов по изображениям\n\n"
                "Определяет переднюю и заднюю часть вагона на фотографии.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "System",
            "description": "Системные эндпоинты (health check)"
        },
        {
            "name": "Prediction",
            "description": "Эндпоинты для классификации изображений"
        }
    ]
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
static_dir = Path(__file__).parent / "static"
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
        "health": "/health",
        "api_health": f"{settings.API_V1_PREFIX}/health"
    }


@app.get("/health")
async def root_health_check():
    """
    Health check эндпоинт для Hugging Face Spaces
    Проверяет состояние приложения и загрузку модели
    """
    try:
        from app.models.wagon_model import get_classifier
        classifier = get_classifier()
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "device": classifier.device,
            "version": settings.VERSION
        }
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "model_loaded": False,
            "error": str(e),
            "version": settings.VERSION
        }


@app.on_event("startup")
async def startup_event():
    """Загрузка модели при старте"""
    logger.info("=" * 50)
    logger.info(f"Запуск {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Порт: {os.getenv('PORT', '7860')} (HF Spaces использует порт 7860)")
    
    # Проверяем доступность GPU (теперь torch импортирован)
    gpu_available = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
    logger.info(f"Режим: {'GPU' if gpu_available else 'CPU'}")
    logger.info("=" * 50)
    
    # Проверяем существование модели
    logger.info(f"Путь к модели: {settings.MODEL_PATH}")
    
    if not os.path.exists(settings.MODEL_PATH):
        logger.warning(f"⚠️ Модель не найдена: {settings.MODEL_PATH}")
        logger.info("Пожалуйста, обучите модель командой: python train_model.py")
    else:
        try:
            # Предварительная загрузка модели
            from app.models.wagon_model import get_classifier
            classifier = get_classifier()
            logger.info(f"✅ Модель загружена на устройство: {classifier.device}")
            logger.info(f"📋 Доступные классы: {classifier.class_names}")
            logger.info(f"📋 Русские названия: {classifier.class_names_ru}")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке модели: {e}")
            import traceback
            logger.error(traceback.format_exc())


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("Остановка API сервиса")


# БЛОК ДЛЯ ЛОКАЛЬНОГО ЗАПУСКА
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )