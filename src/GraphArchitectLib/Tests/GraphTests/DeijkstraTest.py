import pytest
from graph_architect.Algorithms.Graph.SPT.Dijkstra import DijkstraSPath
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW

# Фикстура тестового графа и алгоритма Дейкстры
@pytest.fixture
def setup_graph():
    # Создание тестового графа
    graph = GraphW(6)  # Граф из 6 вершин
    graph.add_edge(0, 1, 7)
    graph.add_edge(0, 2, 9)
    graph.add_edge(0, 5, 14)
    graph.add_edge(1, 2, 10)
    graph.add_edge(1, 3, 15)
    graph.add_edge(2, 3, 11)
    graph.add_edge(2, 5, 2)
    graph.add_edge(3, 4, 6)
    graph.add_edge(4, 5, 9)

    # Создание алгоритма Дейкстры
    dijkstra = DijkstraSPath(graph, 0)  # Начало в вершине 0
    return dijkstra

def test_distances(setup_graph):
    """Тест на проверку правильности расстояний до вершин"""
    expected_distances = [0, 7, 9, 20, 26, 11]
    assert setup_graph.distances == expected_distances

def test_shortest_path_to_vertex_4(setup_graph):
    """Тест на проверку кратчайшего пути до вершины 4"""
    path = setup_graph.edges

    # Восстановим путь от 4 до 0
    result_path = []
    current_vertex = 4
    while current_vertex is not None:
        edge = path[current_vertex]
        if edge:
            result_path.append((edge.start_v, edge.end_v))
            current_vertex = edge.start_v
        else:
            break

    result_path.reverse()

    # Ожидаемый путь: 0 -> 2 -> 5 -> 4
    expected_path = [(0, 2), (2, 3), (3, 4)]
    assert result_path == expected_path

def test_shortest_path_to_vertex_3(setup_graph):
    """Тест на проверку кратчайшего пути до вершины 3"""
    path = setup_graph.edges

    # Восстановим путь от 3 до 0
    result_path = []
    current_vertex = 3
    while current_vertex is not None:
        edge = path[current_vertex]
        if edge:
            result_path.append((edge.start_v, edge.end_v))
            current_vertex = edge.start_v
        else:
            break

    result_path.reverse()

    # Ожидаемый путь: 0 -> 2 -> 3
    expected_path = [(0, 2), (2, 3)]
    assert result_path == expected_path
