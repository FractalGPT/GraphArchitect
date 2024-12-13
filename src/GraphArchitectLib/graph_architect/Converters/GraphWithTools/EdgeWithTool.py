from typing import List

from graph_architect.Algorithms.Graph.BaseEdge import BaseEdge
from graph_architect.Converters.BaseTool import ConverterTool


class ListConverterTool:
    """
    Класс для управления списком инструментов.
    """

    def __init__(self):
        self.tools: List[ConverterTool] = []

    def add(self, tool: ConverterTool):
        """Добавить инструмент в список"""
        self.tools.append(tool)

    def mean_cost(self) -> float:
        """
        Рассчитать среднюю стоимость инструментов.
        Если указана команда, учитывается стоимость для команды.
        """
        if not self.tools:
            return 0.0
        return sum(tool.cost for tool in self.tools) / len(self.tools)


class EdgeWithToolConverter(BaseEdge):
    """
    Ребро с инструментом
    """

    def __init__(self, start_v: int = None, end_v: int = None, tool: ConverterTool = None):
        super().__init__(start_v, end_v)
        self.tools = ListConverterTool()
        if tool:
            self.tools.add(tool)

    def add_tool(self, tool: ConverterTool):
        """Добавить инструмент"""
        self.tools.add(tool)

    def calc_w(self):
        """Расчет веса без учета задачи"""
        self.weight = self.tools.mean_cost()

    def calc_w_with_command(self):
        """Расчет веса"""
        self.weight = self.tools.mean_cost()
