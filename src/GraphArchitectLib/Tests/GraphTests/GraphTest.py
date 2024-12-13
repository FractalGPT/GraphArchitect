import unittest

from graph_architect.Algorithms.Graph.WeightedGraph import GraphW


class TestWeightedGraph(unittest.TestCase):
    def test_add_edge_and_adjacency(self):
        # Создаем граф с 5 вершинами
        graph = GraphW(5)

        # Добавляем ребра
        graph.add_edge(0, 1, 1.5)
        graph.add_edge(1, 2, 2.5)
        graph.add_edge(3, 4, 3.5)

        # Проверяем количество ребер и дуг
        self.assertEqual(graph.e, 3)
        self.assertEqual(graph.arcs, 6)

        # Проверяем смежные вершины
        self.assertEqual(set(graph.adj(0)), {1})
        self.assertEqual(set(graph.adj(1)), {0, 2})
        self.assertEqual(set(graph.adj(3)), {4})
        self.assertEqual(set(graph.adj(4)), {3})

    def test_degree_and_max_degree(self):
        # Создаем граф с 4 вершинами
        graph = GraphW(4)

        # Добавляем ребра
        graph.add_edge(0, 1, 1.0)
        graph.add_edge(1, 2, 2.0)
        graph.add_edge(1, 3, 3.0)

        # Проверяем степень вершины
        self.assertEqual(GraphW.degree(graph, 1), 3)
        self.assertEqual(GraphW.degree(graph, 0), 1)
        self.assertEqual(GraphW.degree(graph, 2), 1)

        # Проверяем максимальную степень
        self.assertEqual(GraphW.max_degree(graph), 3)

    def test_reverse_graph(self):
        # Создаем граф с 3 вершинами
        graph = GraphW(3)

        # Добавляем дуги
        graph.add_arc(0, 1, 1.0)
        graph.add_arc(1, 2, 2.0)

        # Обратный граф
        reversed_graph = graph.reverse()

        # Проверяем обратные дуги
        self.assertEqual(set(reversed_graph.adj(1)), {0})
        self.assertEqual(set(reversed_graph.adj(2)), {1})
        self.assertEqual(reversed_graph.adj(0), [])

    def test_self_loops(self):
        # Создаем граф с 3 вершинами
        graph = GraphW(3)

        # Добавляем петли
        graph.add_edge(0, 0, 1.0)
        graph.add_edge(1, 1, 2.0)

        # Проверяем количество петель
        self.assertEqual(GraphW.num_self_loops(graph), 2)
