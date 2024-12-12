from typing import List, Generic, TypeVar, Iterable
from abc import ABC, abstractmethod

from Algorithms.Graph.BaseEdge import BaseEdge
from Algorithms.Graph.WeightedGraph import GraphW

T = TypeVar('T', bound='BaseEdge')


class ShortestPath(Generic[T], ABC):
    """Абстрактный класс для поиска кратчайшего пути"""

    def __init__(self):
        self.distances = []
        self.edges = []

    @abstractmethod
    def init(self, graph: 'GraphW[T]', start_vertex: int):
        """Инициализация поиска кратчайшего пути"""
        pass

    @abstractmethod
    def distance_to(self, end_vertex: int) -> float:
        """Дистанция до конечной вершины"""
        pass

    @abstractmethod
    def get_edges_from_path(self, end_vertex: int) -> List[T]:
        """Возвращает ребра кратчайшего пути"""
        pass


class ShortestPathTree(Generic[T]):
    """Дерево кратчайших путей"""

    def __init__(self, edges: Iterable[T], distances: Iterable[float]):
        self.distances = list(distances)
        self.edges = list(edges)

    def distance_to(self, end_vertex: int) -> float:
        """Возвращает расстояние до конечной вершины"""
        return self.distances[end_vertex]

    def get_path(self, end_vertex: int) -> List[T]:
        """Возвращает путь до указанной вершины"""
        path = []
        edge = self.edges[end_vertex]
        while edge is not None:
            path.append(edge)
            edge = self.edges[edge.start_v]
        return list(reversed(path))
