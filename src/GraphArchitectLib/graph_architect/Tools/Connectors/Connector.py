import numpy as np
from typing import Optional, Dict, Any, Union, List
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
T_SC = 2.0  # Коэффициент масштабирования для оценки качества соединения
W_Q = 0.5  # Вес для оценки качества
W_C = 0.25  # Вес для оценки стоимости
W_L = 0.25  # Вес для оценки задержки


@dataclass
class EstimatorConfig:
    """Конфигурация для оценщиков"""
    dtype: str = "prompt"
    parameters: Optional[Dict[str, Any]] = None


class Estimator(ABC):
    """Абстрактный базовый класс для оценщиков"""

    def __init__(self, config: EstimatorConfig):
        self.config = config
        self.estimator_id = str(uuid.uuid4())

    @abstractmethod
    def run(self, data: Any) -> float:
        """Запуск оценщика на входных данных"""
        pass

    def validate_input(self, data: Any) -> None:
        """Валидация входных данных"""
        if data is None:
            raise ValueError("Входные данные не могут быть None")
        if not isinstance(data, (np.ndarray, str, dict)):
            raise TypeError(f"Неподдерживаемый тип данных: {type(data)}")


class TimeEstimator(Estimator):
    """Оценщик времени обработки"""

    def __init__(self, config: EstimatorConfig = EstimatorConfig(dtype="prompt")):
        super().__init__(config)

    def run(self, data: Any) -> float:
        self.validate_input(data)
        try:
            # Заглушка для логики оценки времени
            return 1.0 if self.config.dtype == "prompt" else float(np.mean(data))
        except Exception as e:
            logger.error(f"Ошибка оценки времени: {str(e)}")
            raise


class CostEstimator(Estimator):
    """Оценщик стоимости обработки"""

    def __init__(self, config: EstimatorConfig = EstimatorConfig(dtype="prompt")):
        super().__init__(config)

    def run(self, data: Any) -> float:
        self.validate_input(data)
        try:
            # Заглушка для логики оценки стоимости
            return 0.5 if self.config.dtype == "prompt" else float(np.sum(data))
        except Exception as e:
            logger.error(f"Ошибка оценки стоимости: {str(e)}")
            raise


class QualityEstimator(Estimator):
    """Оценщик качества соединения"""

    def __init__(self, config: EstimatorConfig = EstimatorConfig(dtype="vector")):
        super().__init__(config)

    def run(self, data: Any) -> float:
        self.validate_input(data)
        try:
            # Заглушка для логики оценки качества
            return 0.8 if self.config.dtype == "prompt" else float(np.max(data))
        except Exception as e:
            logger.error(f"Ошибка оценки качества: {str(e)}")
            raise


@dataclass
class DataType:
    """Тип данных с свойствами и методом сравнения"""
    complex_type: str = "structured"
    subtype: str = "text"
    properties: Optional[Dict[str, Any]] = None
    properties_compare_method: str = "include"

    def can_connect(self, target: 'DataType') -> bool:
        """Проверка возможности соединения двух типов данных"""
        if self.complex_type != target.complex_type:
            return False
        if self.subtype != target.subtype:
            return False
        if self.properties_compare_method == "include":
            if not self.properties or not target.properties:
                return True
            return all(k in target.properties and target.properties[k] == v
                       for k, v in self.properties.items())
        return True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataType':
        """Создание DataType из словаря"""
        return cls(
            complex_type=data.get("complexType", "structured"),
            subtype=data.get("subtype", "text"),
            properties=data.get("properties"),
            properties_compare_method=data.get("propertiesCompareMethod", "include")
        )


@dataclass
class SemanticType:
    """Семантический тип данных с свойствами и методом сравнения"""
    semantic_category: str = "raw"
    properties: Optional[Dict[str, Any]] = None
    properties_compare_method: str = "include"

    def can_connect(self, target: 'SemanticType') -> bool:
        """Проверка возможности соединения двух семантических типов"""
        if self.semantic_category != target.semantic_category:
            return False
        if self.properties_compare_method == "include":
            if not self.properties or not target.properties:
                return True
            return all(k in target.properties and target.properties[k] == v
                       for k, v in self.properties.items())
        return True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticType':
        """Создание SemanticType из словаря"""
        return cls(
            semantic_category=data.get("semanticCategory", "raw"),
            properties=data.get("properties"),
            properties_compare_method=data.get("propertiesCompareMethod", "include")
        )


class BaseConnector:
    """Базовый класс для коннекторов данных"""

    def __init__(
            self,
            data_type: Optional[DataType] = None,
            semantic_type: Optional[SemanticType] = None,
            knowledge_domain: str = "general",
            connector_type: str = "input_connector",
            time_estimator: Optional[TimeEstimator] = None,
            cost_estimator: Optional[CostEstimator] = None,
            quality_estimator: Optional[QualityEstimator] = None
    ):
        self.connector_id = str(uuid.uuid4())
        self.connector_type = connector_type
        self.data_type = data_type or DataType()
        self.semantic_type = semantic_type or SemanticType()
        self.knowledge_domain = knowledge_domain
        self.time_estimator = time_estimator
        self.cost_estimator = cost_estimator
        self.quality_estimator = quality_estimator

        if any([time_estimator, cost_estimator, quality_estimator]):
            self._validate_estimators()

    def _validate_estimators(self) -> None:
        """Валидация корректной инициализации всех необходимых оценщиков"""
        if not all([self.time_estimator, self.cost_estimator, self.quality_estimator]):
            raise ValueError("Все оценщики должны быть предоставлены, если указан хотя бы один")
        if not isinstance(self.time_estimator, TimeEstimator):
            raise TypeError("time_estimator должен быть экземпляром TimeEstimator")
        if not isinstance(self.cost_estimator, CostEstimator):
            raise TypeError("cost_estimator должен быть экземпляром CostEstimator")
        if not isinstance(self.quality_estimator, QualityEstimator):
            raise TypeError("quality_estimator должен быть экземпляром QualityEstimator")

    def can_connect(self, target_connector: 'BaseConnector') -> bool:
        """Проверка возможности соединения с целевым коннектором"""
        try:
            return (self.data_type.can_connect(target_connector.data_type) and
                    self.semantic_type.can_connect(target_connector.semantic_type) and
                    # Учет общей категории
                    (self.knowledge_domain == target_connector.knowledge_domain or
                     target_connector.knowledge_domain == "general"))

        except Exception as e:
            logger.error(f"Ошибка проверки соединения: {str(e)}")
            return False

    def get_connection_quality(
            self,
            raw_data: Any,
            vector_data: Optional[np.ndarray] = None
    ) -> float:
        """Расчет показателя качества соединения"""
        if not all([self.time_estimator, self.cost_estimator, self.quality_estimator]):
            raise ValueError("Для расчета качества соединения необходимы все оценщики")

        try:
            # Выбор соответствующих данных на основе типа оценщика
            q_data = vector_data if self.quality_estimator.config.dtype == "vector" else raw_data
            c_data = vector_data if self.cost_estimator.config.dtype == "vector" else raw_data
            l_data = vector_data if self.time_estimator.config.dtype == "vector" else raw_data

            # Расчет метрик
            quality = self.quality_estimator.run(q_data)
            cost = self.cost_estimator.run(c_data)
            latency = self.time_estimator.run(l_data)

            # Расчет показателя качества соединения
            quality_score = T_SC * (W_Q * quality - W_C * cost)
            latency_factor = W_L * np.log(latency + 2)

            if latency_factor == 0:
                logger.warning("Фактор задержки равен нулю, возвращается только показатель качества")
                return quality_score

            return quality_score / latency_factor

        except Exception as e:
            logger.error(f"Ошибка расчета качества соединения: {str(e)}")
            raise

    @classmethod
    def from_dict(cls, data: Dict[str, Any], connector_type: str = "input_connector") -> 'BaseConnector':
        """Создание коннектора из словаря"""
        try:
            data_type = DataType.from_dict(data.get("dataType", {}))
            semantic_type = SemanticType.from_dict(data.get("semanticType", {}))
            knowledge_domain = data.get("knowledgeDomain", "general")

            return cls(
                data_type=data_type,
                semantic_type=semantic_type,
                knowledge_domain=knowledge_domain,
                connector_type=connector_type,
                time_estimator=None,
                cost_estimator=None,
                quality_estimator=None
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга коннектора из словаря: {str(e)}")
            raise

    @staticmethod
    def parse_task(json_data: Union[str, Dict[str, Any]]) -> Dict[str, 'BaseConnector']:
        """Парсинг коннекторов из описания задачи ЕЯИ"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data

            connectors = {}
            for key, value in data.items():
                if key in ["input_connector", "output_connector"]:
                    connectors[key] = BaseConnector.from_dict(value, connector_type=key)
                else:
                    logger.warning(f"Неизвестный тип коннектора: {key}")
            return connectors
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            raise

    def __str__(self) -> str:
        return (f"Коннектор(id={self.connector_id}, тип={self.connector_type}, "
                f"домен={self.knowledge_domain})")