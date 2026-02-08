"""
Сравнительные тесты алгоритмов графа.

Тестирует все алгоритмы на разных размерах графов:
- Dijkstra (кратчайший путь)
- A* (с эвристикой)
- Yen (топ-K путей)
- ACO (муравьиный алгоритм)

Измеряет производительность и качество результатов.
"""

import sys
from pathlib import Path
import time

grapharchitect_path = Path(__file__).parent.parent.parent.parent / "src" / "GraphArchitectLib"
sys.path.insert(0, str(grapharchitect_path))

import pytest
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.pathfinding_algorithm import PathfindingAlgorithm
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.entities.base_tool import BaseTool
from grapharchitect.entities.connectors.connector import Connector


class BenchmarkTool(BaseTool):
    """Инструмент для бенчмарка."""
    
    def __init__(self, tool_id, input_fmt, output_fmt, reputation):
        super().__init__()
        self.metadata.tool_name = f"Tool-{tool_id}"
        self.metadata.reputation = reputation
        
        input_parts = input_fmt.split("|")
        output_parts = output_fmt.split("|")
        
        self.input = Connector(input_parts[0], input_parts[1])
        self.output = Connector(output_parts[0], output_parts[1])
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Success"


def create_realistic_tool_graph(n_tools):
    """
    Создать реалистичный граф инструментов.
    
    Структура:
    - Несколько уровней (слоев) преобразований
    - Множественные инструменты на каждом уровне
    - Разные репутации для разнообразия
    
    Args:
        n_tools: Желаемое количество инструментов
        
    Returns:
        Список инструментов, embedding service
    """
    embedding = SimpleEmbeddingService(dimension=384)
    
    # Форматы по слоям
    layer_formats = [
        ["text|question", "text|query"],
        ["text|category", "text|findings"],
        ["text|outline", "text|data"],
        ["text|content", "text|analysis"],
        ["text|draft", "text|report"],
        ["text|polished", "text|answer"]
    ]
    
    tools = []
    tool_id = 0
    
    # Создаем инструменты между слоями
    for layer_idx in range(len(layer_formats) - 1):
        current_formats = layer_formats[layer_idx]
        next_formats = layer_formats[layer_idx + 1]
        
        # Количество инструментов на этот переход
        tools_per_transition = max(1, n_tools // (len(layer_formats) * len(current_formats)))
        
        for input_fmt in current_formats:
            for output_fmt in next_formats:
                for _ in range(tools_per_transition):
                    if tool_id >= n_tools:
                        break
                    
                    # Разные репутации
                    import random
                    reputation = random.uniform(0.65, 0.95)
                    
                    tool = BenchmarkTool(tool_id, input_fmt, output_fmt, reputation)
                    tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
                    
                    tools.append(tool)
                    tool_id += 1
                
                if tool_id >= n_tools:
                    break
            
            if tool_id >= n_tools:
                break
        
        if tool_id >= n_tools:
            break
    
    return tools[:n_tools], embedding


class TestAlgorithmsComparison:
    """Сравнение всех алгоритмов графа."""
    
    @pytest.fixture(scope="class", params=[20, 50, 100])
    def tool_graph(self, request):
        """Создание графов разного размера."""
        n_tools = request.param
        tools, embedding = create_realistic_tool_graph(n_tools)
        
        return {
            "tools": tools,
            "embedding": embedding,
            "size": n_tools
        }
    
    def test_dijkstra_algorithm(self, tool_graph):
        """Тест алгоритма Dijkstra."""
        finder = GraphStrategyFinder()
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tool_graph["tools"],
            start_format="text|question",
            end_format="text|answer",
            algorithm=PathfindingAlgorithm.DIJKSTRA,
            limit=1
        )
        
        elapsed = time.time() - start
        
        print(f"\n  Dijkstra [{tool_graph['size']} tools]: {elapsed*1000:.2f}ms")
        print(f"    Найдено путей: {len(strategies)}")
        
        if strategies:
            print(f"    Длина пути: {len(strategies[0])} шагов")
        
        # Производительность
        assert elapsed < 0.5  # Должно быть быстро
    
    def test_astar_algorithm(self, tool_graph):
        """Тест алгоритма A*."""
        finder = GraphStrategyFinder()
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tool_graph["tools"],
            start_format="text|question",
            end_format="text|answer",
            algorithm=PathfindingAlgorithm.ASTAR,
            limit=1
        )
        
        elapsed = time.time() - start
        
        print(f"\n  A* [{tool_graph['size']} tools]: {elapsed*1000:.2f}ms")
        print(f"    Найдено путей: {len(strategies)}")
        
        # A* должен быть как минимум не медленнее Dijkstra
        assert elapsed < 0.5
    
    def test_yen_algorithm(self, tool_graph):
        """Тест алгоритма Yen (топ-K путей)."""
        finder = GraphStrategyFinder()
        
        # Тест с разными K
        for k in [3, 5, 10]:
            start = time.time()
            
            strategies = finder.find_strategies(
                tools=tool_graph["tools"],
                start_format="text|question",
                end_format="text|answer",
                algorithm=PathfindingAlgorithm.YEN,
                limit=k
            )
            
            elapsed = time.time() - start
            
            print(f"\n  Yen k={k} [{tool_graph['size']} tools]: {elapsed*1000:.2f}ms")
            print(f"    Найдено путей: {len(strategies)}")
            
            # Yen медленнее но должно быть приемлемо
            assert elapsed < 2.0  # Для топ-10 на 100 инструментах
            
            # Проверка уникальности путей
            if len(strategies) > 1:
                path1 = [t.metadata.tool_name for t in strategies[0]]
                path2 = [t.metadata.tool_name for t in strategies[1]]
                # Пути должны отличаться
                assert path1 != path2 or len(path1) != len(path2)
    
    def test_aco_algorithm(self, tool_graph):
        """Тест муравьиного алгоритма."""
        finder = GraphStrategyFinder()
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tool_graph["tools"],
            start_format="text|question",
            end_format="text|answer",
            algorithm=PathfindingAlgorithm.ANT_COLONY,
            limit=5
        )
        
        elapsed = time.time() - start
        
        print(f"\n  ACO [{tool_graph['size']} tools]: {elapsed*1000:.2f}ms")
        print(f"    Найдено путей: {len(strategies)}")
        
        # ACO вероятностный, может быть медленнее
        assert elapsed < 5.0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
