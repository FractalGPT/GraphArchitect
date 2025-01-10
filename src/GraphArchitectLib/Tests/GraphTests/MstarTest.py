import pytest
import math
from graph_architect.Algorithms.Graph.SPT.Mstar import MstarPath
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW


@pytest.fixture
def setup_graph():
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

    return graph


@pytest.fixture
def other_graph():
    graph = GraphW(9)
    graph.add_edge(0, 1, 3)
    graph.add_edge(0, 6, 5)
    graph.add_edge(1, 0, 3)
    graph.add_edge(1, 2, 7)
    graph.add_edge(1, 4, 2)
    graph.add_edge(2, 4, 11)
    graph.add_edge(2, 1, 7)
    graph.add_edge(2, 5, 1)
    graph.add_edge(2, 3, 9)
    graph.add_edge(3, 2, 9)
    graph.add_edge(3, 5, 6)
    graph.add_edge(3, 8, 1)
    graph.add_edge(4, 1, 2)
    graph.add_edge(4, 6, 8)
    graph.add_edge(4, 7, 9)
    graph.add_edge(4, 2, 11)
    graph.add_edge(5, 7, 10)
    graph.add_edge(5, 2, 1)
    graph.add_edge(5, 3, 6)
    graph.add_edge(5, 8, 7)
    graph.add_edge(6, 0, 5)
    graph.add_edge(6, 4, 8)
    graph.add_edge(6, 7, 6)
    graph.add_edge(7, 6, 6)
    graph.add_edge(7, 4, 9)
    graph.add_edge(7, 5, 10)
    graph.add_edge(7, 8, 4)
    graph.add_edge(8, 7, 4)
    graph.add_edge(8, 5, 7)
    graph.add_edge(8, 3, 1)
    return graph

def test_primitive_shortest_path_to_vertex_4(setup_graph):
    """Тест на проверку кратчайшего пути до вершины 4 с использованием обычной эвристики."""
    graph = setup_graph
    mstar = MstarPath(graph)
    start_vertex = 0
    end_vertex = 4
    result_path = mstar.find_path(start_vertex,end_vertex)
    expected_path = [(0, 2), (2, 3), (3, 4)]
    assert result_path == expected_path

#def test_primitive_shortest_path_to_vertex_3(setup_graph):
#    """Тест на проверку кратчайшего пути до вершины 3 с использованием евклидовой эвристики."""
#    graph = setup_graph
#    mstar = MstarPath(graph)
#    start_vertex = 0
#    end_vertex = 3
#    result_path = mstar.find_path(start_vertex,end_vertex)
#    expected_path = [(0, 2), (2, 3)]
#    assert result_path == expected_path

#def test_shortest_path_to_vertex_5(other_graph):
#    """Тест на проверку кратчайшего пути до вершины 4 с использованием обычной эвристики."""
#    graph = other_graph
#    mstar = MstarPath(graph)
#    start_vertex = 0
#    end_vertex = 5
#    result_path = mstar.find_path(start_vertex,end_vertex)
#    expected_path = [(0, 1),(1, 2), (2, 5)]
#    assert result_path == expected_path

#def test_shortest_path_to_vertex_5(other_graph):
#    """Тест на проверку кратчайшего пути до вершины 4 с использованием обычной эвристики."""
#    graph = other_graph
#    mstar = MstarPath(graph)
#    start_vertex = 0
#    end_vertex = 5
#    result_path = mstar.find_path(start_vertex,end_vertex)
#    expected_path = [(0, 1),(1, 2), (2, 5)]
#    assert result_path == expected_path
