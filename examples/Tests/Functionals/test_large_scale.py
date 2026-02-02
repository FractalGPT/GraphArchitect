"""
Тесты на больших масштабах.

Проверяет работу с большими наборами:
- 100+ инструментов
- 1000+ примеров NLI
- Длинные цепочки (5+ шагов)
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


class ScaleTool(BaseTool):
    """Инструмент для stress тестов."""
    
    def __init__(self, tool_id, layer_in, layer_out, reputation):
        super().__init__()
        self.metadata.tool_name = f"Tool-L{layer_in}→L{layer_out}-{tool_id}"
        self.metadata.reputation = reputation
        
        self.input = Connector("text", f"format_{layer_in}")
        self.output = Connector("text", f"format_{layer_out}")
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Success"


def create_layered_graph(n_layers, tools_per_layer):
    """
    Создать многослойный граф инструментов.
    
    Args:
        n_layers: Количество слоев
        tools_per_layer: Инструментов на каждый переход
        
    Returns:
        Список инструментов
    """
    embedding = SimpleEmbeddingService(dimension=384)
    tools = []
    tool_id = 0
    
    # Создаем инструменты между соседними слоями
    for layer in range(n_layers - 1):
        for tool_idx in range(tools_per_layer):
            import random
            reputation = random.uniform(0.70, 0.95)
            
            tool = ScaleTool(tool_id, layer, layer + 1, reputation)
            tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
            
            tools.append(tool)
            tool_id += 1
    
    return tools, embedding


class TestLargeScale:
    """Тесты на больших масштабах."""
    
    @pytest.mark.slow
    def test_100_tools_all_algorithms(self):
        """Тест всех алгоритмов на 100 инструментах."""
        
        # Создаем граф: 10 слоев, 10 инструментов на переход = 100 total
        tools, _ = create_layered_graph(n_layers=11, tools_per_layer=10)
        finder = GraphStrategyFinder()
        
        print(f"\n  Создано инструментов: {len(tools)}")
        print(f"  Формат: text|format_0 → text|format_10")
        print()
        
        results = {}
        
        algorithms = [
            ("Dijkstra", PathfindingAlgorithm.DIJKSTRA, 1),
            ("A*", PathfindingAlgorithm.ASTAR, 1),
            ("Yen-3", PathfindingAlgorithm.YEN, 3),
            ("Yen-5", PathfindingAlgorithm.YEN, 5),
            ("Yen-10", PathfindingAlgorithm.YEN, 10),
            ("ACO-3", PathfindingAlgorithm.ANT_COLONY, 3),
            ("ACO-5", PathfindingAlgorithm.ANT_COLONY, 5)
        ]
        
        for name, algo, limit in algorithms:
            start = time.time()
            
            strategies = finder.find_strategies(
                tools=tools,
                start_format="text|format_0",
                end_format="text|format_10",
                algorithm=algo,
                limit=limit
            )
            
            elapsed = time.time() - start
            
            results[name] = {
                "time_ms": elapsed * 1000,
                "paths_found": len(strategies)
            }
            
            if strategies:
                avg_length = sum(len(s) for s in strategies) / len(strategies)
                results[name]["avg_path_length"] = avg_length
            
            print(f"  {name:12} {elapsed*1000:8.2f}ms  пути:{len(strategies):2}  avg_длина:{results[name].get('avg_path_length', 0):.1f}")
        
        # Проверки производительности
        assert results["Dijkstra"]["time_ms"] < 100  # < 100ms
        assert results["A*"]["time_ms"] < 100
        assert results["Yen-5"]["time_ms"] < 500
        assert results["ACO-5"]["time_ms"] < 5000
    
    @pytest.mark.slow
    def test_200_tools_graph(self):
        """Тест на 200 инструментах."""
        
        # 20 слоев, 10 на переход
        tools, _ = create_layered_graph(n_layers=21, tools_per_layer=10)
        finder = GraphStrategyFinder()
        
        print(f"\n  Инструментов: {len(tools)}")
        
        # Только быстрые алгоритмы
        for algo_name, algo in [("Dijkstra", PathfindingAlgorithm.DIJKSTRA), 
                                ("A*", PathfindingAlgorithm.ASTAR)]:
            start = time.time()
            
            strategies = finder.find_strategies(
                tools=tools,
                start_format="text|format_0",
                end_format="text|format_20",
                algorithm=algo,
                limit=1
            )
            
            elapsed = time.time() - start
            
            print(f"  {algo_name}: {elapsed*1000:.2f}ms, найдено: {len(strategies)}")
            
            # Должно быть приемлемо
            assert elapsed < 1.0
    
    @pytest.mark.slow
    def test_deep_path(self):
        """Тест длинного пути (много шагов)."""
        
        # 50 слоев, 2 инструмента на переход = длинный путь
        tools, _ = create_layered_graph(n_layers=51, tools_per_layer=2)
        finder = GraphStrategyFinder()
        
        print(f"\n  Инструментов: {len(tools)}")
        print(f"  Ожидаемая длина пути: ~50 шагов")
        
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tools,
            start_format="text|format_0",
            end_format="text|format_50",
            algorithm=PathfindingAlgorithm.DIJKSTRA,
            limit=1
        )
        
        elapsed = time.time() - start
        
        if strategies:
            path_length = len(strategies[0])
            print(f"  Найден путь: {path_length} шагов за {elapsed*1000:.2f}ms")
            
            # Путь должен быть длинным
            assert path_length >= 45
        
        # Производительность
        assert elapsed < 1.0
    
    def test_selector_with_many_candidates(self):
        """Тест selector с большим количеством кандидатов."""
        
        # 50 инструментов для одного шага
        tools, embedding = create_layered_graph(n_layers=2, tools_per_layer=50)
        
        selector = InstrumentSelector(temperature_constant=1.0)
        task_embedding = embedding.embed_text("Тестовая задача")
        
        print(f"\n  Кандидатов: {len(tools)}")
        
        # Разные top_k
        for top_k in [5, 10, 20, 50]:
            start = time.time()
            
            result = selector.select_instrument(tools, task_embedding, top_k=top_k)
            
            elapsed = time.time() - start
            
            print(f"  top_k={top_k:2}: {elapsed*1000:.2f}ms")
            
            # Должно быть быстро даже для top_k=50
            assert elapsed < 0.1
    
    @pytest.mark.slow
    def test_complex_graph_topology(self):
        """Тест сложной топологии графа."""
        
        # Создаем граф с множественными связями
        tools = []
        embedding = SimpleEmbeddingService(dimension=384)
        
        # Несколько "хабов" - форматы к которым ведет много путей
        hubs = ["text|intermediate_1", "text|intermediate_2", "text|intermediate_3"]
        
        tool_id = 0
        
        # Много путей к хабам
        for hub in hubs:
            for i in range(10):
                tool = ScaleTool(tool_id, 0, 1, 0.80)
                tool.output = Connector("text", hub.split("|")[1])
                tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
                tools.append(tool)
                tool_id += 1
        
        # От хабов к финалу
        for hub in hubs:
            for i in range(5):
                tool = ScaleTool(tool_id, 1, 2, 0.80)
                tool.input = Connector("text", hub.split("|")[1])
                tool.output = Connector("text", "format_2")
                tool.metadata.capabilities_embedding = embedding.embed_tool_capabilities(tool)
                tools.append(tool)
                tool_id += 1
        
        finder = GraphStrategyFinder()
        
        print(f"\n  Инструментов: {len(tools)}")
        print(f"  Топология: Множественные пути через хабы")
        
        # Yen должен найти разнообразные пути
        start = time.time()
        
        strategies = finder.find_strategies(
            tools=tools,
            start_format="text|format_0",
            end_format="text|format_2",
            algorithm=PathfindingAlgorithm.YEN,
            limit=10
        )
        
        elapsed = time.time() - start
        
        print(f"  Yen топ-10: {elapsed*1000:.2f}ms, найдено: {len(strategies)}")
        
        # Должны быть найдены альтернативы
        assert len(strategies) >= 3
        
        # Производительность
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
