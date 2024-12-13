class BaseEdge:
    """
    Абстрактный класс ребра
    """

    def __init__(self, start_v: int = None, end_v: int = None, weight: float = None):
        self.start_v = start_v
        self.end_v = end_v
        self.weight = weight

    def either(self) -> int:
        """Вернуть начальную вершину"""
        return self.start_v

    def other(self, vertex: int) -> int:
        """Вернуть другую вершину"""
        if vertex == self.start_v:
            return self.end_v
        return self.start_v

    def __lt__(self, other: 'BaseEdge') -> bool:
        return self.weight < other.weight

    def __eq__(self, other: 'BaseEdge') -> bool:
        return self.weight == other.weight

    def __gt__(self, other: 'BaseEdge') -> bool:
        return self.weight > other.weight
