import numpy as np
from typing import Generic, TypeVar, List, Tuple

from graph_architect.Algorithms.Graph.WeightedGraph import GraphW,BaseEdge

T = TypeVar('T', bound='BaseEdge')

class MstarPath(Generic[T]):
    """Алгоритм m*"""
    def __init__(self, graph: 'GraphW[T]', excepted_vertexes = []):
        self.graph = graph
        self.nodes = list(graph.adjacency_list.keys())
        self.__init_matrix(graph)
        self.excepted_vertexes = set(excepted_vertexes)

    #DEBUG
    def print_matrix(self,matrix):
        """
        Выводит матрицу в удобочитаемом виде.
        Элементы округляются до 3 знаков после запятой.

        :param matrix: list of lists (двумерный массив)
        """
        print("\n")
        for row in matrix:
            formatted_row = "  ".join(f"{value:7.3f}" for value in row)
            print(formatted_row)

    # Публичный метод для добавления узла.
    def add_exception(self,vertex):
        """Метод для добавления узла, который необходимо обходить."""
        n = self.graph.v
        if vertex > n or vertex < 0:
            raise ValueError("MstarPath Incorrect Number")
        self.excepted_vertexes.add(vertex)

    def __adjacency_matrix(self,graph:'GraphW[T]'):
        n = graph.v
        matrix = np.zeros((n, n))

        for edges in graph.adjacency_list.values():
            for edge in edges:
                if edge.weight == 0:
                    weight = 0
                else:
                    weight = 1/edge.weight
                matrix[edge.start_v, edge.end_v] = weight
                matrix[edge.end_v,edge.start_v] = weight
        for i in range(n):
            accumulator = 0
            for j in range(n):
                if j == i:
                    continue
                accumulator += matrix[i][j]
            matrix[i][i] = -accumulator
        return matrix

    #TODO добавить опцию интерактивного добавления элементов(инструментов)
    def __init_matrix(self,graph:'GraphW[T]',deviation_data = [0,0.1]):
        """Инициализация M* матрицы (инверсированная матрица смежности с поправками)."""
        self.raw_mstar_matrix = self.__adjacency_matrix(graph)
        n = graph.v
        # Данные отклонения хранят на какой позиции в матрице необходимо изменить содержимое параметров
        # 0 - позиция [0..n], при -1 пропускается , 0.1 - изменяемое значение [0;1].
        # По дефолту рекомендуется брать 0.1 на значение в первой диагонали. с параметрами можно играться
        position = deviation_data[0]
        value = deviation_data[1]
        if position > n or position < -1:
            raise ValueError("position in deviation data incorrect")
        if value < 0 or value > 1:
            raise ValueError("position in deviation data incorrect")
        if deviation_data[0] != -1:
            self.raw_mstar_matrix[position][position] += value
        self.print_matrix(self.raw_mstar_matrix)
        det = np.linalg.det(self.raw_mstar_matrix)
        if det == 0:
            raise ValueError("Unable to build matrix")
        self.mstar_matrix = self.reverse()

    def reverse(self):
        return np.linalg.inv(self.raw_mstar_matrix)

    # Основная функция поиска пути на основе имеющихся данных об инструментах.
    def find_path(self, vertex_start: int, vertex_end: int):
        """
        Поиск пути между вершинами start и end.
        vertex_start - начальная вершина
        vertex_end - начальная вершина
        # Также используются изменяемые поля класса.
        excepted_vertexes - исключаемые вершины
        self.graph - граф
        self.mstar_matrix - матрица m*
        """
        if vertex_start == vertex_end:
            return [vertex_start]

        if vertex_start not in self.graph.adjacency_list or vertex_end not in self.graph.adjacency_list:
            raise ValueError("No vertex in the graph")

        #start_row = self.mstar_matrix[vertex_start]
        end_row = self.mstar_matrix[vertex_end]

        current = vertex_start
        path = []

        #visited = []
        while current != vertex_end:
            neighbors = self.graph.adjacency_list[current]

            highest_value = -float('inf')
            next_node = None
            print("current ",current)

            for edge in neighbors:

                # Отсеивание соседей, которые ведут к искомой вершние, смотрим только куда можно попасть.
                start = edge.start_v
                if start != current:
                    continue

                # Завершение при дохождении до последней точки.
                neighbor = edge.end_v
                if vertex_end == neighbor:
                    next_node = neighbor
                    break

                # Обход нежелательных соседей. Алгоритм не будет учитывать их.
                if neighbor in list(self.excepted_vertexes):
                    continue

                # Обработка прохождений одинаковых соседей.
                #if neighbor in visited:
                #    continue

                # Основная логика алгоритма, расчет параметров и выбор оптимального пути
                weight = edge.weight
                value = (end_row[current] - end_row[neighbor]) / weight
                if value > highest_value:
                    highest_value = value
                    next_node = neighbor
                    #visited.append(neighbor)

            # Выход из алгоритма, при ненахождении пути
            if next_node is None:
                raise ValueError("Path not found")

            # Добавляем исходный шаг в путь.
            # TODO Если алгоритм имеет опции к прохождению без массива visited, То необходимо добавить
            # Оптимизацию найденного пути, и избегания циклов внутри полученного графа.
            path.append((current,next_node))
            current = next_node

        return path