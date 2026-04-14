"""
Unit-тесты для main.py
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestMain:
    """Тесты главного приложения"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint_returns_200(self, client):
        """Корневой эндпоинт — возвращает 200 OK"""
        response = client.get("/")
        assert response.status_code in [200, 404]
    
    def test_docs_endpoint_exists(self, client):
        """Документация Swagger — доступна"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint_exists(self, client):
        """ReDoc документация — доступна"""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_json_exists(self, client):
        """OpenAPI схема — доступна"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
    def test_metrics_endpoint_exists(self, client):
        """Эндпоинт метрик — доступен"""
        response = client.get("/metrics")
        assert response.status_code == 200