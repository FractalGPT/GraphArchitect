from typing import List, Any

from graph_architect.Converters.BaseTool import ConverterTool


class IRunnerConverter:
    """
    Интерфейс запуска стратегии
    """

    def run(self, input_data: Any, tool_strategy: List['ConverterTool']) -> Any:
        """
        Запуск стратегии
        """
        raise NotImplementedError("Метод должен быть реализован")
