import heapq


class IndexPriorityQueueMin:
    """Минимальная приоритетная очередь"""

    def __init__(self, max_size: int):
        self.heap = []
        self.position_map = {}

    def insert(self, index: int, priority: float):
        """Добавляет элемент с приоритетом"""
        heapq.heappush(self.heap, (priority, index))
        self.position_map[index] = priority

    def del_min_get_index(self) -> int:
        """Удаляет и возвращает индекс с минимальным приоритетом"""
        while self.heap:
            priority, index = heapq.heappop(self.heap)
            if index in self.position_map and self.position_map[index] == priority:
                del self.position_map[index]
                return index
        raise IndexError("Priority queue is empty")

    def update(self, index: int, priority: float):
        """Обновляет приоритет существующего элемента"""
        self.insert(index, priority)

    def is_contain(self, index: int) -> bool:
        """Проверяет наличие элемента в очереди"""
        return index in self.position_map

    def is_empty(self) -> bool:
        """Проверяет, пуста ли очередь"""
        return not self.position_map
