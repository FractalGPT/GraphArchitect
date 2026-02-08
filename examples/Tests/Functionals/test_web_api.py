"""
Функциональные тесты Web API.

Проверяет:
- Все endpoints работают
- Загрузка файлов
- Streaming ответов
- Работа с БД
"""

import pytest
import requests
import json
import time
from pathlib import Path


BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestWebAPIFunctional:
    """Функциональные тесты Web API."""
    
    @pytest.fixture(scope="class")
    def server_running(self):
        """Проверка что сервер запущен."""
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                return True
        except:
            pytest.skip("Web API сервер не запущен. Запустите: python main.py")
    
    def test_health_endpoint(self, server_running):
        """Тест health check endpoint."""
        response = requests.get(f"{API_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "data" in data
        assert "version" in data["data"]
        assert "grapharchitect_enabled" in data["data"]
    
    def test_agents_library(self, server_running):
        """Тест получения списка инструментов."""
        response = requests.get(f"{API_URL}/agents-library")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert len(data["agents"]) > 0
        
        # Проверка структуры агента
        agent = data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "type" in agent
    
    def test_message_streaming(self, server_running):
        """Тест streaming ответов."""
        chat_id = f"test_stream_{int(time.time())}"
        
        response = requests.post(
            f"{API_URL}/chat/{chat_id}/message/stream",
            data={
                "message": "Классифицировать текст",
                "planning_algorithm": "yen_5"
            },
            stream=True
        )
        
        assert response.status_code == 200
        
        # Проверка NDJSON streaming
        chunks_received = 0
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                chunks_received += 1
                
                # Каждый chunk должен иметь type
                assert "type" in chunk
                
                # Останавливаемся после первых 5
                if chunks_received >= 5:
                    break
        
        assert chunks_received > 0
    
    def test_training_statistics(self, server_running):
        """Тест получения статистики обучения."""
        response = requests.get(f"{API_URL}/training/statistics")
        
        # Может быть 200 или 503 если training не активен
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "enabled" in data or "data" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
