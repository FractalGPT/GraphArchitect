"""
Тесты производительности.

Проверяет:
- Скорость алгоритмов
- Время выполнения
- Масштабируемость
"""

import sys
from pathlib import Path
import time

grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.pathfinding_algorithm import PathfindingAlgorithm
from grapharchitect.services.selection.instrument_selector import InstrumentSelector
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.entities.base_tool import BaseTool
from grapharchitect.entities.connectors.connector import Connector


class PerfTool(BaseTool):
    """Инструмент для тестов производительности."""
    
    def __init__(self, name, input_fmt, output_fmt):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = 0.80
        
        input_parts = input_fmt.split("|")
        output_parts = output_fmt.split("|")
        
        self.input = Connector(input_parts[0], input_parts[1])
        self.output = Connector(output_parts[0], output_parts[1])
    
    def execute(self, input_data):
        return "Success"


class TestPerformance:
    """Тесты производительности."""
    
    @pytest.fixture
    def large_tool_set(self):
        """Создание большого набора инструментов."""
        embedding = SimpleEmbeddingService(dimension=384)
        
        tools = []
        formats = [
            ("text", "question"), ("text", "answer"),
            ("text", "category"), ("text", "content"),
            ("text", "outline"), ("text", "summary"),
            ("text", "data"), ("text", "report")
        ]
        
        # Создаем 20 инструментов
        for i in range(20):
            input_fmt = formats[i % len(formats)]
            output_fmt = formats[(i + 1) % len(formats)]
            
            tool = PerfTool(
                f"Tool-{i}",
                f"{input_fmt[0]}|{input_fmt[1]}",
                f"{output_fmt[0]}|{output_fmt[1]}"
            )
            
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
            tools.append(tool)
        
        return tools, embedding
    
    def test_dijkstra_performance(self, large_tool_set):
        """Тест скорости Dijkstra."""
        tools, _ = large_tool_set
        
        finder = GraphStrategyFinder()
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tools,
            start_format="text|question",
            end_format="text|answer",
            algorithm=PathfindingAlgorithm.DIJKSTRA,
            limit=1
        )
        
        elapsed = time.time() - start
        
        # Должно быть быстро (< 0.1s для 20 инструментов)
        assert elapsed < 0.1
        print(f"\n  Dijkstra: {elapsed*1000:.2f}ms для {len(tools)} инструментов")
    
    def test_yen_performance(self, large_tool_set):
        """Тест скорости Yen algorithm."""
        tools, _ = large_tool_set
        
        finder = GraphStrategyFinder()
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tools,
            start_format="text|question",
            end_format="text|answer",
            algorithm=PathfindingAlgorithm.YEN,
            limit=5
        )
        
        elapsed = time.time() - start
        
        # Должно быть приемлемо (< 1s для топ-5 путей)
        assert elapsed < 1.0
        print(f"\n  Yen (k=5): {elapsed*1000:.2f}ms для {len(tools)} инструментов")
    
    def test_selector_performance(self, large_tool_set):
        """Тест скорости выбора инструмента."""
        tools, embedding = large_tool_set
        
        # Берем подмножество для выбора
        subset = tools[:10]
        
        selector = InstrumentSelector(temperature_constant=1.0)
        task_embedding = embedding.embed_text("Тестовая задача")
        
        start = time.time()
        
        result = selector.select_instrument(subset, task_embedding, top_k=5)
        
        elapsed = time.time() - start
        
        # Softmax должен быть быстрым (< 0.01s)
        assert elapsed < 0.01
        print(f"\n  Softmax selection: {elapsed*1000:.2f}ms для {len(subset)} инструментов")
    
    def test_embedding_performance(self):
        """Тест скорости генерации эмбеддингов."""
        embedding = SimpleEmbeddingService(dimension=384)
        
        test_texts = [
            "Короткий текст",
            "Средний текст с несколькими словами",
            "Длинный текст " * 50  # ~500 символов
        ]
        
        for text in test_texts:
            start = time.time()
            
            emb = embedding.embed_text(text)
            
            elapsed = time.time() - start
            
            # SimpleEmbedding должен быть мгновенным
            assert elapsed < 0.001
            assert len(emb) == 384
    
    def test_scalability_with_many_tools(self):
        """Тест масштабируемости с большим количеством инструментов."""
        embedding = SimpleEmbeddingService(dimension=384)
        finder = GraphStrategyFinder()
        
        # Тест с разным количеством инструментов
        for n_tools in [10, 20, 50]:
            tools = []
            
            for i in range(n_tools):
                tool = PerfTool(f"Tool-{i}", "text|question", "text|answer")
                tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
                tools.append(tool)
            
            start = time.time()
            
            strategies = finder.find_strategies(
                tools=tools,
                start_format="text|question",
                end_format="text|answer",
                algorithm=PathfindingAlgorithm.DIJKSTRA,
                limit=1
            )
            
            elapsed = time.time() - start
            
            print(f"\n  {n_tools} инструментов: {elapsed*1000:.2f}ms")
            
            # Должно быть линейное или лучше масштабирование
            # Для 50 инструментов < 0.5s
            if n_tools == 50:
                assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
