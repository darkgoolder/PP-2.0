"""
Метрики для мониторинга приложения
Сбор статистики о работе API и модели
"""

import logging
import re
import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware  # <-- ДОБАВИТЬ

logger = logging.getLogger(__name__)

# ============ HTTP Метрики ============

# Счетчик HTTP запросов
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

# Длительность HTTP запросов
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Активные запросы в данный момент
HTTP_ACTIVE_REQUESTS = Gauge("http_active_requests", "Number of active HTTP requests")

# ============ Метрики модели ============

# Количество предсказаний
MODEL_PREDICTIONS_TOTAL = Counter(
    "model_predictions_total", "Total number of predictions made", ["predicted_class"]
)

# Время выполнения предсказания
MODEL_PREDICTION_DURATION = Histogram(
    "model_prediction_seconds", "Time taken for model prediction in seconds", ["device"]
)

# Статус загрузки модели (1 = загружена, 0 = не загружена)
MODEL_LOADED = Gauge("model_loaded", "Whether the model is loaded (1) or not (0)")

# Время загрузки модели
MODEL_LOAD_TIME = Gauge("model_load_seconds", "Time taken to load the model in seconds")

# Уверенность предсказаний
MODEL_PREDICTION_CONFIDENCE = Histogram(
    "model_prediction_confidence",
    "Confidence of model predictions",
    ["predicted_class"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99],
)


class MetricsMiddleware(
    BaseHTTPMiddleware
):  # <-- ИСПРАВЛЕНО: наследуемся от BaseHTTPMiddleware
    """
    Middleware для сбора метрик HTTP запросов
    Автоматически собирает статистику по каждому запросу
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:  # <-- ИСПРАВЛЕНО: dispatch вместо __call__
        method = request.method
        endpoint = request.url.path

        # Увеличиваем счетчик активных запросов
        HTTP_ACTIVE_REQUESTS.inc()

        # Замеряем время выполнения
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            status = 500
            raise
        finally:
            # Записываем метрики
            duration = time.time() - start_time

            # Очищаем endpoint от динамических частей для уменьшения количества метрик
            clean_endpoint = _clean_endpoint(endpoint)

            HTTP_REQUEST_DURATION.labels(
                method=method, endpoint=clean_endpoint
            ).observe(duration)

            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=clean_endpoint, status=status
            ).inc()

            HTTP_ACTIVE_REQUESTS.dec()


def _clean_endpoint(endpoint: str) -> str:
    """
    Очищает endpoint от динамических параметров
    Например: /api/v1/predict/123 -> /api/v1/predict/{id}
    """
    # Простая очистка - заменяем цифровые ID на {id}
    cleaned = re.sub(r"/\d+", "/{id}", endpoint)
    return cleaned


async def get_metrics():
    """
    Эндпоинт для сбора метрик Prometheus
    Возвращает все метрики в формате text/plain
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_prediction_metrics(
    class_name: str, confidence: float, device: str, duration: float
):
    """
    Запись метрик предсказания

    Args:
        class_name: Предсказанный класс
        confidence: Уверенность предсказания (0-1)
        device: Устройство выполнения (cpu/cuda)
        duration: Время выполнения в секундах
    """
    MODEL_PREDICTIONS_TOTAL.labels(predicted_class=class_name).inc()
    MODEL_PREDICTION_DURATION.labels(device=device).observe(duration)
    MODEL_PREDICTION_CONFIDENCE.labels(predicted_class=class_name).observe(confidence)


def set_model_loaded(loaded: bool, load_time: float = 0):
    """
    Установка статуса загрузки модели

    Args:
        loaded: Загружена ли модель
        load_time: Время загрузки в секундах (если loaded=True)
    """
    MODEL_LOADED.set(1 if loaded else 0)
    if loaded and load_time > 0:
        MODEL_LOAD_TIME.set(load_time)
