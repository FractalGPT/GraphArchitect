from typing import Generic, TypeVar,Callable, Any, List, Tuple

from graph_architect.Algorithms.Graph.WeightedGraph import GraphW
from graph_architect.Algorithms.PriorityQueueMin import IndexPriorityQueueMin

T = TypeVar('T', bound='BaseEdge')


class AstarPath(Generic[T]):
    """Алгоритм a*"""
    """Основное отличие от Дейкстры заключается в использовании эвристической функции, для 'Жадного' перебора значений"""
    def __init__(self, graph: 'GraphW[T]', vertex_start: int, heuristic: Callable[[Any], Any], *args):
        """
        graph - граф
        vertex_start - начальная вершина
        heuristic - эвристическая функция
        """
        self.edges = [None] * graph.v  # Ребра кратчайшего пути
        self.distances = [float('inf')] * graph.v  # Расстояния до вершин
        self.heuristics = [float('inf')] * graph.v  # Эвристические оценки
        self.min_pq = IndexPriorityQueueMin(graph.v)

        self.distances[vertex_start] = 0
        self.heuristics[vertex_start] = heuristic(vertex_start,*args)
        self.min_pq.insert(vertex_start, self.distances[vertex_start] + self.heuristics[vertex_start])

        counter = 0
        while not self.min_pq.is_empty():
            v = self.min_pq.del_min_get_index()
            # Идея, закончить поиск если дошли до конечной точки. Дать выбор, использовать ускоренную версию или нет.
            # TODO придумать более разумный критерий остановки. Для ускорения работы алгоритма.
            #if v == coordinates.get('target'):
            #    break
            for edge in graph.adj_ew(v):  # Метод adj_ew возвращает рёбра
                self._update(edge, heuristic, *args)
                counter += 1

    def _update(self, edge: T, heuristic: Callable[[Any,Any], Any], *args):
            """Ослабление ребра"""
            v_in = edge.start_v
            v_out = edge.other(v_in)
            #print("ВЕРШИНА X",v_in, "ВЕРШИНА Y",v_out )
            weight = self.distances[v_in] + edge.weight

            if self.distances[v_out] > weight:
                self.distances[v_out] = weight
                self.edges[v_out] = edge
                self.heuristics[v_out] = heuristic(v_out,*args)

                # Приоритет зависит от f = g + h
                priority = self.distances[v_out] + self.heuristics[v_out]
                #print("В ИЗМЕНЕНИИ ПРИОРИТЕТА", priority)

                if self.min_pq.is_contain(v_out):
                    self.min_pq.update(v_out, priority)
                else:
                    self.min_pq.insert(v_out, priority)

    def get_path(self, vertex_end: int) -> List[Tuple[int, int]]:
            """Восстановление пути"""
            result_path = []
            current_vertex = vertex_end
            while current_vertex is not None:
                edge = self.edges[current_vertex]
                if edge:
                    result_path.append((edge.start_v, edge.end_v))
                    current_vertex = edge.start_v
                else:
                    break
            result_path.reverse()
            return result_path