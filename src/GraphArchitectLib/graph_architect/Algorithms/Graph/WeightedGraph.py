from typing import List, TypeVar, Generic
from collections import defaultdict

from graph_architect.Algorithms.Graph.BaseEdge import BaseEdge

T = TypeVar('T', bound='BaseEdge')


class GraphW(Generic[T]):
    """
    Взвешенный граф
    """

    def __init__(self, num_v: int):
        self.v = num_v
        self.e = 0
        self.arcs = 0
        self.adjacency_list = defaultdict(list)

    def add_edge_w(self, edge: T):
        """Добавить ребро между двумя вершинами"""
        v = edge.either()
        w = edge.other(v)
        self.adjacency_list[v].append(edge)
        self.adjacency_list[w].append(edge)
        self.e += 1
        self.arcs += 2

    def add_edge(self, i: int, j: int, weight: float = 1):
        """Добавить ребро между двумя вершинами"""
        edge = BaseEdge(start_v=i, end_v=j, weight=weight)
        self.add_edge_w(edge)

    def add_arc_w(self, edge: T):
        """Добавить дугу между двумя вершинами"""
        v = edge.either()
        self.adjacency_list[v].append(edge)
        self.e += 1
        self.arcs += 1

    def add_arc(self, i: int, j: int, weight: float = 1):
        """Добавить дугу между двумя вершинами"""
        edge = BaseEdge(start_v=i, end_v=j, weight=weight)
        self.add_arc_w(edge)

    def adj(self, i: int) -> List[int]:
        """Смежные вершины"""
        return [edge.other(i) for edge in self.adjacency_list[i]]

    def adj_ew(self, i: int) -> List[T]:
        """Смежные ребра"""
        return self.adjacency_list[i]

    @staticmethod
    def degree(graph: 'GraphW', i: int) -> int:
        """Степень связи"""
        return len(graph.adj(i))

    @staticmethod
    def max_degree(graph: 'GraphW') -> int:
        """Максимальная связь в графе"""
        return max(GraphW.degree(graph, i) for i in range(graph.v))

    @staticmethod
    def average_degree(graph: 'GraphW') -> float:
        """Средняя связь"""
        return 2.0 * graph.e / graph.v

    @staticmethod
    def num_self_loops(graph: 'GraphW') -> int:
        """Число петель в графе"""
        count = 0
        for i in range(graph.v):
            for edge in graph.adj_ew(i):
                if edge.start_v == edge.end_v:
                    count += 1
        return count // 2

    def reverse(self) -> 'GraphW':
        """Меняет направления в графе на противоположные"""
        reversed_graph = GraphW(self.v)
        for i in range(self.v):
            for edge in self.adj_ew(i):
                reversed_graph.add_arc(edge.end_v, edge.start_v, edge.weight)
        return reversed_graph

    def __str__(self):
        """Строковое представление графа"""
        result = []
        for i in range(self.v):
            for edge in self.adjacency_list[i]:
                result.append(f"{edge.start_v} -> {edge.end_v} [weight={edge.weight}]")
        return "\n".join(result)
