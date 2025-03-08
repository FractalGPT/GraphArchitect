from typing import List

from graph_architect.BaseTool import ConverterTool


class IStrategyDecoder:
    """
    Интерфейс декодера стратегии решений
    """

    def get_tools(self, strategy: List[List['ConverterTool']]) -> List['ConverterTool']:
        """
        Получение инструментов из общей стратегии
        """
        raise NotImplementedError("Метод должен быть реализован")

