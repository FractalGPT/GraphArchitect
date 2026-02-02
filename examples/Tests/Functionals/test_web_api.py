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
        
        assert data["status"] == "success"
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
        assert "cost" in agent
    
    def test_create_chat(self, server_running):
        """Тест создания чата."""
        chat_id = f"test_chat_{int(time.time())}"
        
        # Отправка сообщения создает чат автоматически
        response = requests.post(
            f"{API_URL}/chat/{chat_id}/message",
            data={
                "message": "Тестовое сообщение",
                "planning_algorithm": "dijkstra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "chat_id" in data
        assert data["chat_id"] == chat_id
    
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
    
    def test_document_upload(self, server_running):
        """Тест загрузки документа."""
        chat_id = f"test_doc_{int(time.time())}"
        
        # Создаем тестовый файл
        test_file_content = b"Test document content for GraphArchitect"
        
        response = requests.post(
            f"{API_URL}/chat/{chat_id}/document",
            files={"file": ("test.txt", test_file_content, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "document_id" in data
        assert "filename" in data
        assert data["filename"] == "test.txt"
        assert data["chat_id"] == chat_id
    
    def test_get_documents(self, server_running):
        """Тест получения списка документов."""
        chat_id = f"test_docs_{int(time.time())}"
        
        # Загружаем документ
        test_file = b"Test content"
        requests.post(
            f"{API_URL}/chat/{chat_id}/document",
            files={"file": ("doc.txt", test_file, "text/plain")}
        )
        
        # Получаем список
        response = requests.get(f"{API_URL}/chat/{chat_id}/documents")
        
        assert response.status_code == 200
        documents = response.json()
        
        assert isinstance(documents, list)
        assert len(documents) >= 1
    
    def test_training_statistics(self, server_running):
        """Тест получения статистики обучения."""
        response = requests.get(f"{API_URL}/training/statistics")
        
        # Может быть 200 или 503 если training не активен
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "enabled" in data or "data" in data
    
    def test_workflow_creation(self, server_running):
        """Тест создания workflow."""
        chat_id = f"test_workflow_{int(time.time())}"
        
        response = requests.post(
            f"{API_URL}/chat/{chat_id}/workflow",
            data={
                "user_message": "Создать статью",
                "request_type": "text",
                "planning_algorithm": "yen_5",
                "use_streaming": False
            }
        )
        
        assert response.status_code == 200
        workflow = response.json()
        
        assert "name" in workflow
        assert "steps" in workflow
        assert len(workflow["steps"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
