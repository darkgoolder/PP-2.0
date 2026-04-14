"""
Unit-тесты для метрик
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.infrastructure.metrics import MetricsMiddleware, get_metrics


class TestMetrics:
    """Тесты метрик Prometheus"""
    
    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        app.add_api_route("/metrics", get_metrics, methods=["GET"])
        return app
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    def test_metrics_endpoint_returns_data(self, client):
        """Эндпоинт /metrics — возвращает метрики"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "python_info" in response.text
    
    def test_middleware_records_request(self, client):
        """Middleware — записывает метрики запроса"""
        response = client.get("/test")
        assert response.status_code == 200
        
        metrics_response = client.get("/metrics")
        assert "http_requests_total" in metrics_response.text
        
    def test_metrics_endpoint_returns_correct_content_type(self, client):
        """Эндпоинт /metrics — возвращает правильный Content-Type"""
        response = client.get("/metrics")
        assert response.headers.get("content-type").startswith("text/plain")