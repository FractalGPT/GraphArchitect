"""
Тесты надежности системы.

Проверяет:
- Обработку ошибок
- Graceful degradation
- Fallback механизмы
- Устойчивость к некорректным входным данным
"""

import sys
from pathlib import Path

grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator
from grapharchitect.services.execution.execution_status import ExecutionStatus
from grapharchitect.services.selection.instrument_selector import InstrumentSelector
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.entities.task_definition import TaskDefinition
from grapharchitect.entities.connectors.connector import Connector
from grapharchitect.entities.base_tool import BaseTool


class BrokenTool(BaseTool):
    """Инструмент который выбрасывает ошибку."""
    
    def __init__(self):
        super().__init__()
        self.metadata.tool_name = "Broken Tool"
        self.metadata.reputation = 0.90
        self.input = Connector("text", "question")
        self.output = Connector("text", "answer")
    
    def execute(self, input_data):
        raise RuntimeError("Симуляция ошибки инструмента")


class SlowTool(BaseTool):
    """Медленный инструмент."""
    
    def __init__(self):
        super().__init__()
        self.metadata.tool_name = "Slow Tool"
        self.metadata.reputation = 0.85
        self.metadata.mean_time_answer = 10.0  # 10 секунд
        self.input = Connector("text", "question")
        self.output = Connector("text", "answer")
    
    def execute(self, input_data):
        import time
        time.sleep(0.1)  # Небольшая задержка для теста
        return "Медленный ответ"


class NormalTool(BaseTool):
    """Нормальный инструмент."""
    
    def __init__(self):
        super().__init__()
        self.metadata.tool_name = "Normal Tool"
        self.metadata.reputation = 0.80
        self.input = Connector("text", "question")
        self.output = Connector("text", "answer")
    
    def execute(self, input_data):
        return "Нормальный ответ"


class TestSystemReliability:
    """Тесты надежности и устойчивости системы."""
    
    @pytest.fixture
    def orchestrator(self):
        """Создание orchestrator."""
        embedding = SimpleEmbeddingService(dimension=384)
        selector = InstrumentSelector(temperature_constant=1.0)
        finder = GraphStrategyFinder()
        
        return ExecutionOrchestrator(embedding, selector, finder), embedding
    
    def test_empty_tools_list(self, orchestrator):
        """Тест с пустым списком инструментов."""
        exec_orchestrator, _ = orchestrator
        
        task = TaskDefinition(
            description="Задача без инструментов",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "answer"),
            input_data="Test"
        )
        
        context = exec_orchestrator.execute_task(task, [], path_limit=1, top_k=1)
        
        # Система должна обработать корректно (не крашнуться)
        assert context is not None
        assert context.status != ExecutionStatus.COMPLETED
    
    def test_tool_execution_error_handling(self, orchestrator):
        """Тест обработки ошибок в инструментах."""
        exec_orchestrator, embedding = orchestrator
        
        # Создаем инструменты (один ломаный, один нормальный)
        broken = BrokenTool()
        normal = NormalTool()
        
        tools = [broken, normal]
        
        for tool in tools:
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        task = TaskDefinition(
            description="Тест обработки ошибок",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "answer"),
            input_data="Test"
        )
        
        # Выполнение - система должна либо использовать Normal, либо обработать ошибку
        context = exec_orchestrator.execute_task(task, tools, path_limit=1, top_k=2)
        
        # Система не должна крашнуться
        assert context is not None
    
    def test_invalid_connector_formats(self, orchestrator):
        """Тест некорректных форматов коннекторов."""
        exec_orchestrator, embedding = orchestrator
        
        tool = NormalTool()
        tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        # Задача с несуществующими коннекторами
        task = TaskDefinition(
            description="Некорректная задача",
            input_connector=Connector("unknown", "format"),
            output_connector=Connector("invalid", "type"),
            input_data="Test"
        )
        
        context = exec_orchestrator.execute_task(task, [tool], path_limit=1, top_k=1)
        
        # Система должна обработать (не крашнуться)
        assert context is not None
    
    def test_very_long_input(self, orchestrator):
        """Тест очень длинного входа."""
        exec_orchestrator, embedding = orchestrator
        
        tool = NormalTool()
        tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        # Очень длинный текст (10000 символов)
        long_input = "A" * 10000
        
        task = TaskDefinition(
            description="Задача с длинным входом",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "answer"),
            input_data=long_input
        )
        
        context = exec_orchestrator.execute_task(task, [tool], path_limit=1, top_k=1)
        
        # Должно обработаться без ошибок
        assert context is not None
        assert context.result is not None
    
    def test_concurrent_executions(self, orchestrator):
        """Тест параллельных выполнений."""
        exec_orchestrator, embedding = orchestrator
        
        tool = NormalTool()
        tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        # Запускаем несколько задач подряд
        results = []
        
        for i in range(5):
            task = TaskDefinition(
                description=f"Задача {i}",
                input_connector=Connector("text", "question"),
                output_connector=Connector("text", "answer"),
                input_data=f"Input {i}"
            )
            
            context = exec_orchestrator.execute_task(task, [tool], path_limit=1, top_k=1)
            results.append(context)
        
        # Все должны выполниться
        assert len(results) == 5
        assert all(r is not None for r in results)
    
    def test_zero_reputation_tool(self, orchestrator):
        """Тест инструмента с нулевой репутацией."""
        exec_orchestrator, embedding = orchestrator
        
        tool = NormalTool()
        tool.metadata.reputation = 0.01  # Минимальная репутация
        tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        task = TaskDefinition(
            description="Тест низкой репутации",
            input_connector=Connector("text", "question"),
            output_connector=Connector("text", "answer"),
            input_data="Test"
        )
        
        context = exec_orchestrator.execute_task(task, [tool], path_limit=1, top_k=1)
        
        # Должен выполниться даже с низкой репутацией
        assert context.status == ExecutionStatus.COMPLETED
    
    def test_missing_intermediate_tools(self, orchestrator):
        """Тест отсутствия промежуточных инструментов."""
        exec_orchestrator, embedding = orchestrator
        
        # Только начальный и конечный, нет промежуточных
        tool_start = NormalTool()
        tool_start.metadata.tool_name = "Start"
        tool_start.input = Connector("text", "question")
        tool_start.output = Connector("text", "intermediate")
        
        tool_end = NormalTool()
        tool_end.metadata.tool_name = "End"
        tool_end.input = Connector("text", "intermediate")
        tool_end.output = Connector("text", "answer")
        
        # НЕТ инструмента для text|other → text|intermediate
        
        tools = [tool_start, tool_end]
        for tool in tools:
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
        
        # Задача требует промежуточный формат
        task = TaskDefinition(
            description="Задача с промежуточным форматом",
            input_connector=Connector("text", "other"),  # Другой формат!
            output_connector=Connector("text", "answer"),
            input_data="Test"
        )
        
        context = exec_orchestrator.execute_task(task, tools, path_limit=1, top_k=1)
        
        # Путь не найден, но система не крашится
        assert context is not None
        assert context.status == ExecutionStatus.FAILED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
