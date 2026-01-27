"""Модуль естественно-языкового интерфейса (ЕЯИ / NLI)"""

from .nli_dataset_item import NLIDatasetItem
from .knn_few_shot_retriever import KNNFewShotRetriever, ScoredExample, DatasetStatistics
from .connector_info_aggregator import ConnectorInfoAggregator
from .natural_language_interface import NaturalLanguageInterface, NLIParseResult

__all__ = [
    'NLIDatasetItem',
    'KNNFewShotRetriever',
    'ScoredExample',
    'DatasetStatistics',
    'ConnectorInfoAggregator',
    'NaturalLanguageInterface',
    'NLIParseResult'
]
