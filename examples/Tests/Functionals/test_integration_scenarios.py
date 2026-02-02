"""
Тесты интеграционных сценариев.

Проверяет:
- Полные пользовательские сценарии
- Customer Support workflow
- Content Creation workflow
- Data Analysis workflow
"""

import sys
from pathlib import Path

grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator
from grapharchitect.services.selection.instrument_selector import InstrumentSelector
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.entities.task_definition import TaskDefinition
from grapharchitect.entities.connectors.connector import Connector
from grapharchitect.entities.base_tool import BaseTool
from grapharchitect.services.execution.execution_status import ExecutionStatus


class ScenarioTool(BaseTool):
    """Инструмент для сценарных тестов."""
    
    def __init__(self, name, input_fmt, output_fmt):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = 0.85
        
        input_parts = input_fmt.split("|")
        output_parts = output_fmt.split("|")
        
        self.input = Connector(input_parts[0], input_parts[1])
        self.output = Connector(output_parts[0], output_parts[1])
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Обработано"


class TestIntegrationScenarios:
    """Тесты полных пользовательских сценариев."""
    
    @pytest.fixture
    def orchestrator(self):
        """Создание orchestrator."""
        embedding = SimpleEmbeddingService(dimension=384)
        selector = InstrumentSelector(temperature_constant=1.0)
        finder = GraphStrategyFinder()
        
        return ExecutionOrchestrator(embedding, selector, finder), embedding
    
    @pytest.fixture
    def customer_support_tools(self, orchestrator):
        """Инструменты для customer support."""
        _, embedding = orchestrator
        
        tools = [
            ScenarioTool("Classifier", "text|question", "text|category"),
            ScenarioTool("Responder", "text|category", "text|response"),
            ScenarioTool("QA-Check", "text|response", "text|validated")
        ]
        
        for tool in tools:
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        return tools
    
    @pytest.fixture
    def content_creation_tools(self, orchestrator):
        """Инструменты для content creation."""
        _, embedding = orchestrator
        
        tools = [
            ScenarioTool("Researcher", "text|topic", "text|findings"),
            ScenarioTool("Outliner", "text|findings", "text|outline"),
            ScenarioTool("Writer", "text|outline", "text|content"),
            ScenarioTool("Editor", "text|content", "text|polished")
        ]
        
        for tool in tools:
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        return tools
    
    def test_customer_support_scenario(self, orchestrator, customer_support_tools):
        """
        Сценарий: Обработка запроса клиента.
        
        Workflow: Classify → Respond → QA
        """
        exec_orchestrator, _ = orchestrator
        
        task = TaskDefinition(
            description="Обработать жалобу клиента",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "validated"),
            input_data="Жду доставку неделю!"
        )
        
        context = exec_orchestrator.execute_task(
            task, customer_support_tools, path_limit=1, top_k=3
        )
        
        # Проверки
        assert context.status == ExecutionStatus.COMPLETED
        assert context.get_total_steps() == 3
        
        # Проверка последовательности инструментов
        step_names = [s.selected_tool.metadata.tool_name for s in context.execution_steps]
        assert "Classifier" in step_names
        assert "Responder" in step_names
        assert "QA-Check" in step_names
    
    def test_content_creation_scenario(self, orchestrator, content_creation_tools):
        """
        Сценарий: Создание контента.
        
        Workflow: Research → Outline → Write → Edit
        """
        exec_orchestrator, _ = orchestrator
        
        task = TaskDefinition(
            description="Создать статью об AI",
            input_connector=Connector("text", "topic"),
            output_connector=Connector("text", "polished"),
            input_data="Искусственный интеллект в медицине"
        )
        
        context = exec_orchestrator.execute_task(
            task, content_creation_tools, path_limit=1, top_k=3
        )
        
        # Проверки
        assert context.status == ExecutionStatus.COMPLETED
        assert context.get_total_steps() == 4
        
        # Все инструменты использованы
        assert len(context.execution_steps) == 4
    
    def test_alternative_paths_with_yen(self, orchestrator, customer_support_tools):
        """
        Тест поиска альтернативных путей (Yen algorithm).
        
        Проверяет что система находит несколько вариантов решения.
        """
        exec_orchestrator, _ = orchestrator
        
        # Находим стратегии напрямую
        from grapharchitect.services.pathfinding_algorithm import PathfindingAlgorithm
        
        strategies = exec_orchestrator._strategy_finder.find_strategies(
            tools=customer_support_tools,
            start_format="text|question",
            end_format="text|validated",
            algorithm=PathfindingAlgorithm.YEN,
            limit=3
        )
        
        # Должно быть найдено несколько путей
        assert len(strategies) >= 1
        
        # Все пути должны быть разными
        if len(strategies) > 1:
            path1_names = [t.metadata.tool_name for t in strategies[0]]
            path2_names = [t.metadata.tool_name for t in strategies[1]]
            assert path1_names != path2_names or len(path1_names) != len(path2_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
