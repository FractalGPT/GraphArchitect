import unittest

from graph_architect.Algorithms.Graph.SPT.Dijkstra import DijkstraSPath
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW


class TestDijkstra(unittest.TestCase):
    def setUp(self):
        """Создание тестового графа"""
        self.graph = GraphW(6)  # Граф из 6 вершин
        self.graph.add_edge(0, 1, 7)
        self.graph.add_edge(0, 2, 9)
        self.graph.add_edge(0, 5, 14)
        self.graph.add_edge(1, 2, 10)
        self.graph.add_edge(1, 3, 15)
        self.graph.add_edge(2, 3, 11)
        self.graph.add_edge(2, 5, 2)
        self.graph.add_edge(3, 4, 6)
        self.graph.add_edge(4, 5, 9)

        # Создание алгоритма Дейкстры
        self.dijkstra = DijkstraSPath(self.graph, 0)  # Начало в вершине 0

    def test_distances(self):
        """Тест на проверку правильности расстояний до вершин"""
        self.setUp()
        expected_distances = [0, 7, 9, 20, 26, 11]
        self.assertEqual(self.dijkstra.distances, expected_distances)

    def test_shortest_path_to_vertex_4(self):
        """Тест на проверку кратчайшего пути до вершины 4"""
        self.setUp()
        path = self.dijkstra.edges

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
        self.assertEqual(result_path, expected_path)

    def test_shortest_path_to_vertex_3(self):
        """Тест на проверку кратчайшего пути до вершины 3"""
        self.setUp()
        path = self.dijkstra.edges

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
        self.assertEqual(result_path, expected_path)