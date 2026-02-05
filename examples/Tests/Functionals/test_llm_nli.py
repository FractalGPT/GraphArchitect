"""
Тесты LLM-based NLI сервиса.

Проверяет:
- Парсинг через LLM
- k-NN + few-shot интеграция
- Работу с разными бэкендами
- Точность парсинга
"""

import sys
from pathlib import Path
import os

grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.nli.llm_nli_service import LLMNLIService
from grapharchitect.services.nli.nli_dataset_item import NLIDatasetItem
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.entities.connectors.task_representation import TaskRepresentation
from grapharchitect.entities.connectors.connector import Connector
from grapharchitect.entities.base_tool import BaseTool


class TestLLMNLI:
    """Тесты LLM-based NLI."""
    
    @pytest.fixture
    def embedding_service(self):
        """Embedding service для k-NN."""
        return SimpleEmbeddingService(dimension=384)
    
    @pytest.fixture
    def dataset(self, embedding_service):
        """Тестовый датасет примеров."""
        examples = []
        
        # Классификация
        rep1 = TaskRepresentation()
        rep1.input_connector = Connector("text", "question")
        rep1.output_connector = Connector("text", "category")
        
        examples.append(NLIDatasetItem(
            task_text="Классифицировать текст",
            task_embedding=embedding_service.embed_text("Классифицировать текст"),
            representation=rep1
        ))
        
        # QA
        rep2 = TaskRepresentation()
        rep2.input_connector = Connector("text", "question")
        rep2.output_connector = Connector("text", "answer")
        
        examples.append(NLIDatasetItem(
            task_text="Ответить на вопрос",
            task_embedding=embedding_service.embed_text("Ответить на вопрос"),
            representation=rep2
        ))
        
        return examples
    
    @pytest.fixture
    def tools(self):
        """Тестовые инструменты."""
        class TestTool(BaseTool):
            def __init__(self, name, input_fmt, output_fmt):
                super().__init__()
                self.metadata.tool_name = name
                
                inp = input_fmt.split("|")
                out = output_fmt.split("|")
                
                self.input = Connector(inp[0], inp[1])
                self.output = Connector(out[0], out[1])
            
            def execute(self, input_data):
                return "OK"
        
        return [
            TestTool("Classifier", "text|question", "text|category"),
            TestTool("QA", "text|question", "text|answer")
        ]
    
    def test_llm_nli_initialization(self, embedding_service):
        """Тест инициализации LLM NLI."""
        
        if not os.getenv('OPENROUTER_API_KEY'):
            pytest.skip("OPENROUTER_API_KEY не установлен")
        
        llm_nli = LLMNLIService(
            embedding_service=embedding_service,
            backend="openrouter",
            model_name="openai/gpt-3.5-turbo"
        )
        
        assert llm_nli is not None
        assert llm_nli.is_available()
    
    def test_llm_nli_with_few_shot(self, embedding_service, dataset, tools):
        """Тест парсинга с few-shot примерами из k-NN."""
        
        if not os.getenv('OPENROUTER_API_KEY'):
            pytest.skip("OPENROUTER_API_KEY не установлен")
        
        llm_nli = LLMNLIService(
            embedding_service=embedding_service,
            backend="openrouter",
            model_name="openai/gpt-3.5-turbo",
            k_similar=2
        )
        
        llm_nli.load_dataset(dataset)
        
        # Парсинг похожего запроса (должен найти в k-NN)
        result = llm_nli.parse_task("Определить категорию текста", tools)
        
        assert result.success
        assert result.task_representation is not None
        assert result.task_representation.input_connector.format == "text|question"
        assert result.task_representation.output_connector.format == "text|category"
    
    def test_llm_nli_without_similar_examples(self, embedding_service, dataset, tools):
        """Тест парсинга без похожих примеров (базовый few-shot)."""
        
        if not os.getenv('OPENROUTER_API_KEY'):
            pytest.skip("OPENROUTER_API_KEY не установлен")
        
        llm_nli = LLMNLIService(
            embedding_service=embedding_service,
            backend="openrouter"
        )
        
        llm_nli.load_dataset(dataset)
        
        # Совершенно новый тип задачи (не в датасете)
        result = llm_nli.parse_task(
            "Преобразовать изображение в описание",
            tools
        )
        
        # LLM должен справиться даже без похожих примеров
        assert result.success
        assert result.task_representation is not None
    
    def test_prompt_creation(self, embedding_service, dataset, tools):
        """Тест создания промпта."""
        
        llm_nli = LLMNLIService(
            embedding_service=embedding_service,
            backend="openrouter"
        )
        
        llm_nli.load_dataset(dataset)
        
        # Получаем похожие примеры
        similar = llm_nli._find_similar_examples("Классифицировать текст", k=2)
        
        # Создаем промпт
        prompt = llm_nli._create_few_shot_prompt("Тестовая задача", similar, tools)
        
        # Проверка структуры промпта
        assert "Задача:" in prompt
        assert "Доступные форматы" in prompt
        assert "Примеры:" in prompt
        assert "JSON" in prompt
        
        # Если есть похожие, должны быть в промпте
        if similar:
            assert similar[0].task_text in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
