"""Базовый класс инструмента - основная единица в графе"""

from typing import List, Optional
import math
from abc import ABC, abstractmethod

from .tool_metadata import ToolMetadata
from .connectors.connector import Connector


class BaseTool(ABC):
    """
    Базовый класс инструмента (ранее BaseAgent).
    
    Инструмент преобразует данные из формата входного коннектора
    в формат выходного коннектора. В графе инструменты находятся
    на ребрах между вершинами-коннекторами.
    """
    
    def __init__(self):
        self.input: Connector = Connector()
        self.output: Connector = Connector()
        self.metadata: ToolMetadata = ToolMetadata()
    
    @property
    def reputation(self) -> float:
        """Репутация инструмента (0-1)"""
        return self.metadata.reputation
    
    @reputation.setter
    def reputation(self, value: float):
        self.metadata.reputation = value
    
    @property
    def mean_cost(self) -> float:
        """Средняя стоимость использования"""
        return self.metadata.mean_cost
    
    @mean_cost.setter
    def mean_cost(self, value: float):
        self.metadata.mean_cost = value
    
    def get_graph_weight(self) -> float:
        """
        Расчет веса для графа (LogLoss).
        Чем выше репутация, тем меньше вес (лучше путь).
        
        Returns:
            Вес ребра графа
        """
        safe_reward = max(self.metadata.reputation, 1e-6)
        return -math.log(safe_reward)
    
    def get_logit(self, task_embedding: Optional[List[float]] = None) -> float:
        """
        Вычисление логита (ненормированной оценки качества).
        
        Логит = косинусное_сходство(задача, возможности) + log(репутация)
        
        Args:
            task_embedding: Векторное представление задачи
            
        Returns:
            Логит инструмента для данной задачи
        """
        if task_embedding is None or self.metadata.capabilities_embedding is None:
            return math.log(max(self.metadata.reputation, 1e-6))
        
        # Косинусное сходство + бонус репутации
        similarity = self._cosine_similarity(
            task_embedding, 
            self.metadata.capabilities_embedding
        )
        reputation_bonus = math.log(max(self.metadata.reputation, 1e-6))
        
        return similarity + reputation_bonus
    
    def get_temperature(self, constant_c: float = 1.0) -> float:
        """
        Вычисление температуры для данного инструмента.
        
        Формула: T_k = C * sqrt(D_k* / m_k)
        где:
        - C - константа
        - D_k* - оценка дисперсии оценок инструмента k
        - m_k - объем выборки для обучения инструмента k
        
        Температура обратно пропорциональна корню от объема выборки.
        
        Args:
            constant_c: Константа C
            
        Returns:
            Температура инструмента
        """
        m_k = max(self.metadata.training_sample_size, 1)
        d_k = max(self.metadata.variance_estimate, 1e-6)
        
        return constant_c * math.sqrt(d_k / m_k)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Косинусное сходство между двумя векторами"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def clone(self):
        """Клонирование инструмента"""
        import copy
        return copy.deepcopy(self)
    
    @abstractmethod
    def execute(self, input_data) -> any:
        """
        Выполнить инструмент.
        
        Args:
            input_data: Входные данные
            
        Returns:
            Результат выполнения
        """
        pass
