import pytest
import math
from graph_architect.Algorithms.Graph.SPT.Astar import AstarPath
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW


# Фикстура тестового графа и координат
@pytest.fixture
def setup_graph_and_coordinates():
    # Создание графа
    graph = GraphW(6)
    graph.add_edge(0, 1, 7)
    graph.add_edge(0, 2, 9)
    graph.add_edge(0, 5, 14)
    graph.add_edge(1, 2, 10)
    graph.add_edge(1, 3, 15)
    graph.add_edge(2, 3, 11)
    graph.add_edge(2, 5, 2)
    graph.add_edge(3, 4, 6)
    graph.add_edge(4, 5, 9)

    # Координаты вершин
    coordinates = {
        0: (0, 0),   # Стартовая вершина
        1: (1, 4),
        2: (1, 0),
        3: (2, 5),
        4: (3, 5),
        5: (2, 0),
        'target': 5
    }

    return graph, coordinates


# Эвристические функции
def reverse_heuristic(v: int) -> float:
    """Используем фиксированные эвристики (обратный порядок)."""
    heuristics = list(range(5, -1, -1))  # [5, 4, 3, 2, 1, 0]
    return heuristics[v]

def heuristic(v: int) -> float:
    """Используем фиксированные эвристики (по порядку)."""
    heuristics = list(range(6))  # [0, 1, 2, 3, 4, 5]
    return heuristics[v]

def euclidean_heuristic(v: int, coordinates: dict) -> float:
    """Эвристика (евклидово расстояние)."""
    target = coordinates['target']
    x1, y1 = coordinates[v]
    x2, y2 = coordinates[target]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def test_primitive_distances(setup_graph_and_coordinates):
    """Тест на проверку правильности расстояний до вершин с использованием обычного массива эвристики."""
    graph, _ = setup_graph_and_coordinates
    astar = AstarPath(graph, 0, heuristic)
    expected_distances = [0, 7, 9, 20, 26, 11]
    assert astar.distances == expected_distances


def test_primitive_reverse_distances(setup_graph_and_coordinates):
    """Тест на проверку правильности расстояний до вершин с использованием обратной эвристики."""
    graph, _ = setup_graph_and_coordinates
    astar = AstarPath(graph, 0, reverse_heuristic)
    expected_distances = [0, 7, 9, 20, 26, 11]
    assert astar.distances == expected_distances


def test_euclidean_distances(setup_graph_and_coordinates):
    """Тест на проверку правильности расстояний до вершин с использованием евклидовой эвристики."""
    graph, coordinates = setup_graph_and_coordinates
    astar = AstarPath(graph, 0, euclidean_heuristic, coordinates)
    expected_distances = [0, 7, 9, 20, 26, 11]
    assert astar.distances == expected_distances


def test_primitive_shortest_path_to_vertex_4(setup_graph_and_coordinates):
    """Тест на проверку кратчайшего пути до вершины 4 с использованием обычной эвристики."""
    graph, _ = setup_graph_and_coordinates
    astar = AstarPath(graph, 0, heuristic)
    end_vertex = 4
    result_path = astar.get_path(end_vertex)
    expected_path = [(0, 2), (2, 3), (3, 4)]
    assert result_path == expected_path


def test_shortest_path_to_vertex_3(setup_graph_and_coordinates):
    """Тест на проверку кратчайшего пути до вершины 3 с использованием евклидовой эвристики."""
    graph, coordinates = setup_graph_and_coordinates
    astar = AstarPath(graph, 0, euclidean_heuristic, coordinates)
    end_vertex = 3
    result_path = astar.get_path(end_vertex)
    expected_path = [(0, 2), (2, 3)]
    assert result_path == expected_path
