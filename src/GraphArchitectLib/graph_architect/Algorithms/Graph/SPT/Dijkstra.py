from typing import Generic, TypeVar


from graph_architect.Algorithms.Graph.WeightedGraph import GraphW
from graph_architect.Algorithms.PriorityQueueMin import IndexPriorityQueueMin

T = TypeVar('T', bound='BaseEdge')

class DijkstraSPath(Generic[T]):
    """Алгоритм Дейкстры"""
    def __init__(self, graph: 'GraphW[T]', vertex_start: int):
        self.edges = [None] * graph.v  # Ребра кратчайшего пути
        self.distances = [float('inf')] * graph.v  # Расстояния до вершин
        self.min_pq = IndexPriorityQueueMin(graph.v)

        self.distances[vertex_start] = 0
        self.min_pq.insert(vertex_start, 0)

        while not self.min_pq.is_empty():
            v = self.min_pq.del_min_get_index()
            for edge in graph.adj_ew(v):  # Метод adj_ew возвращает ребра
                self._update(edge)

    def _update(self, edge: T):
        """Ослабление ребра"""
        v_in = edge.start_v
        v_out = edge.other(v_in)
        weight = self.distances[v_in] + edge.weight

        if self.distances[v_out] > weight:
            self.distances[v_out] = weight
            self.edges[v_out] = edge
            if self.min_pq.is_contain(v_out):
                self.min_pq.update(v_out, weight)
            else:
                self.min_pq.insert(v_out, weight)