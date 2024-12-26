import pytest

from graph_architect.Algorithms.Graph.WeightedGraph import GraphW

# --disable-warnings - Отключить варнинги
# Добавить маркер @pytest.mark.graph_add_edge_and_adjacency -> python -m pytest -m graph_add_edge_and_adjacency
# Проверка на вхождение. python -m pytest -k "add_edge"
# Запуск 1-го теста
# python -m pytest Tests/GraphTests/GraphTest.py::test_add_edge_and_adjacency
# Запуск всех тестов из файла.
# python -m pytest Tests/GraphTests/GraphTest.py

def test_add_edge_and_adjacency():
    # Создаем граф с 5 вершинами
    graph = GraphW(5)

    # Добавляем ребра
    graph.add_edge(0, 1, 1.5)
    graph.add_edge(1, 2, 2.5)
    graph.add_edge(3, 4, 3.5)

    # Проверяем количество ребер и дуг
    assert graph.e == 3
    assert graph.arcs == 6

    # Проверяем смежные вершины
    assert set(graph.adj(0)) == {1}
    assert set(graph.adj(1)) == {0, 2}
    assert set(graph.adj(3)) == {4}
    assert set(graph.adj(4)) == {3}


def test_degree_and_max_degree():
    # Создаем граф с 4 вершинами
    graph = GraphW(4)

    # Добавляем ребра
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 2.0)
    graph.add_edge(1, 3, 3.0)

    # Проверяем степень вершины
    assert GraphW.degree(graph, 1) == 3
    assert GraphW.degree(graph, 0) == 1
    assert GraphW.degree(graph, 2) == 1

    # Проверяем максимальную степень
    assert GraphW.max_degree(graph) == 3


def test_reverse_graph():
    # Создаем граф с 3 вершинами
    graph = GraphW(3)

    # Добавляем дуги
    graph.add_arc(0, 1, 1.0)
    graph.add_arc(1, 2, 2.0)

    # Обратный граф
    reversed_graph = graph.reverse()

    # Проверяем обратные дуги
    assert set(reversed_graph.adj(1)) == {0}
    assert set(reversed_graph.adj(2)) == {1}
    assert reversed_graph.adj(0) == []


def test_self_loops():
    # Создаем граф с 3 вершинами
    graph = GraphW(3)

    # Добавляем петли
    graph.add_edge(0, 0, 1.0)
    graph.add_edge(1, 1, 2.0)

    # Проверяем количество петель
    assert GraphW.num_self_loops(graph) == 2
