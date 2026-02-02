"""
End-to-End тест полного workflow.

Проверяет:
- NLI парсинг
- Поиск стратегий
- Выбор инструментов
- Выполнение
- Обучение
"""

import sys
from pathlib import Path

# Добавляем GraphArchitect
grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator
from grapharchitect.services.selection.instrument_selector import InstrumentSelector
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.services.training.training_orchestrator import TrainingOrchestrator
from grapharchitect.services.feedback.simple_critic import SimpleCritic
from grapharchitect.entities.task_definition import TaskDefinition
from grapharchitect.entities.connectors.connector import Connector
from grapharchitect.entities.base_tool import BaseTool
from grapharchitect.services.execution.execution_status import ExecutionStatus


class TestTool(BaseTool):
    """Тестовый инструмент."""
    
    def __init__(self, name, input_fmt, output_fmt, reputation=0.80):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = reputation
        self.metadata.training_sample_size = 10
        self.metadata.variance_estimate = 0.1
        
        input_parts = input_fmt.split("|")
        output_parts = output_fmt.split("|")
        
        self.input = Connector(input_parts[0], input_parts[1])
        self.output = Connector(output_parts[0], output_parts[1])
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Success: {str(input_data)[:50]}"


class TestEndToEndWorkflow:
    """End-to-End тесты полного workflow."""
    
    @pytest.fixture
    def components(self):
        """Создание всех компонентов системы."""
        embedding = SimpleEmbeddingService(dimension=384)
        selector = InstrumentSelector(temperature_constant=1.0)
        finder = GraphStrategyFinder()
        training = TrainingOrchestrator(learning_rate=0.01)
        critic = SimpleCritic()
        
        orchestrator = ExecutionOrchestrator(embedding, selector, finder)
        
        # Набор тестовых инструментов
        tools = [
            TestTool("Classifier-A", "text|question", "text|category", 0.90),
            TestTool("Classifier-B", "text|question", "text|category", 0.85),
            TestTool("QA-System", "text|question", "text|answer", 0.88),
            TestTool("Writer", "text|outline", "text|content", 0.82),
        ]
        
        # Генерация эмбеддингов
        for tool in tools:
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        return {
            "embedding": embedding,
            "selector": selector,
            "finder": finder,
            "orchestrator": orchestrator,
            "training": training,
            "critic": critic,
            "tools": tools
        }
    
    def test_simple_classification_workflow(self, components):
        """Тест простой классификации (1 шаг)."""
        
        # Создание задачи
        task = TaskDefinition(
            description="Классифицировать отзыв клиента",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "category"),
            input_data="Отличный продукт, рекомендую!"
        )
        
        # Выполнение
        context = components["orchestrator"].execute_task(
            task=task,
            available_tools=components["tools"],
            path_limit=1,
            top_k=2
        )
        
        # Проверки
        assert context.status == ExecutionStatus.COMPLETED
        assert context.result is not None
        assert len(context.result) > 0
        assert context.get_total_steps() == 1
        assert len(context.execution_steps) == 1
        
        # Проверка выбора
        step = context.execution_steps[0]
        assert step.selected_tool is not None
        assert step.selected_tool.metadata.tool_name in ["Classifier-A", "Classifier-B"]
        assert 0.0 <= step.selection_result.selection_probability <= 1.0
        assert step.selection_result.temperature > 0
    
    def test_multi_step_workflow(self, components):
        """Тест многошагового workflow (2 шага)."""
        
        # Нужно добавить промежуточный инструмент
        outliner = TestTool("Outliner", "text|topic", "text|outline", 0.85)
        outliner.metadata.capabilities_embedding = components["embedding"].embed_tool_capabilities(outliner)
        
        tools_extended = components["tools"] + [outliner]
        
        # Задача: Topic → Outline → Content
        task = TaskDefinition(
            description="Создать статью",
            input_connector=Connector("text", "topic"),
            output_connector=Connector("text", "content"),
            input_data="Искусственный интеллект"
        )
        
        # Выполнение
        context = components["orchestrator"].execute_task(
            task=task,
            available_tools=tools_extended,
            path_limit=1,
            top_k=3
        )
        
        # Проверки
        assert context.status == ExecutionStatus.COMPLETED
        assert context.get_total_steps() == 2  # Outliner → Writer
        
        # Проверка последовательности
        assert context.execution_steps[0].selected_tool.metadata.tool_name == "Outliner"
        assert context.execution_steps[1].selected_tool.metadata.tool_name == "Writer"
    
    def test_training_updates_reputation(self, components):
        """Тест обучения - репутация обновляется."""
        
        tool = components["tools"][0]
        old_reputation = tool.metadata.reputation
        
        # Выполнение задачи
        task = TaskDefinition(
            description="Классифицировать",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "category"),
            input_data="Тест"
        )
        
        context = components["orchestrator"].execute_task(
            task, components["tools"], path_limit=1, top_k=2
        )
        
        # Оценка
        feedback = components["critic"].evaluate_execution(context)
        
        # Добавление в датасет
        components["training"].add_execution_to_dataset(context, [feedback])
        
        # Обучение
        components["training"].train_all_tools([tool])
        
        # Проверка изменения репутации
        new_reputation = tool.metadata.reputation
        
        # Репутация должна измениться (в любую сторону)
        assert new_reputation != old_reputation
    
    def test_temperature_decreases_with_experience(self, components):
        """Тест снижения температуры с опытом."""
        
        tool = components["tools"][0]
        
        # Увеличиваем sample_size (симулируем опыт)
        initial_sample_size = tool.metadata.training_sample_size
        initial_temp = tool.get_temperature()
        
        # После обучения
        tool.metadata.training_sample_size = initial_sample_size * 10
        
        new_temp = tool.get_temperature()
        
        # Температура должна снизиться
        assert new_temp < initial_temp
    
    def test_no_path_found(self, components):
        """Тест когда путь не найден."""
        
        # Задача с несуществующими коннекторами
        task = TaskDefinition(
            description="Невозможная задача",
            input_connector=Connector("image", "raw"),  # Нет инструментов для image
            output_connector=Connector("audio", "speech"),
            input_data="Test"
        )
        
        # Выполнение
        context = components["orchestrator"].execute_task(
            task, components["tools"], path_limit=1, top_k=2
        )
        
        # Статус должен быть FAILED (путь не найден)
        assert context.status == ExecutionStatus.FAILED
    
    def test_softmax_probabilities_valid(self, components):
        """Тест корректности softmax вероятностей."""
        
        task = TaskDefinition(
            description="Классифицировать",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "category"),
            input_data="Тест"
        )
        
        context = components["orchestrator"].execute_task(
            task, components["tools"], path_limit=1, top_k=2
        )
        
        # Проверка вероятностей
        if context.execution_steps:
            step = context.execution_steps[0]
            prob = step.selection_result.selection_probability
            
            # Вероятность должна быть в диапазоне [0, 1]
            assert 0.0 <= prob <= 1.0
            
            # Температура положительная
            assert step.selection_result.temperature > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
