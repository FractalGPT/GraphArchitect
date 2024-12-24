## НЕ РАБОТАЕТ ###

import unittest
from unittest.mock import MagicMock

from graph_architect.Converters.BaseTool import ConverterTool
from graph_architect.Converters.GraphWithTools.EdgeWithTool import EdgeWithToolConverter
from graph_architect.Converters.GraphWithTools.ToolManager import ManagerConverterTools
from graph_architect.Converters.Strategy.Decoders.IStDecoder import IStrategyDecoder
from graph_architect.Converters.Strategy.Ranners.IRun import IRunnerConverter
from graph_architect.Algorithms.Graph.SPT.Dijkstra import DijkstraSPath
from graph_architect.Algorithms.Graph.SPT.SPTBase import ShortestPathTree
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW



class TestManagerConverterTools(unittest.TestCase):
    """
    Набор тестов для проверки функциональности класса ManagerConverterTools,
    который отвечает за управление инструментами-конвертерами и их стратегиями.
    """

    def setUp(self):
        self.mock_decoder = MagicMock(spec=IStrategyDecoder)
        self.mock_runner = MagicMock(spec=IRunnerConverter)

        # Create an instance of ManagerConverterTools
        self.manager = ManagerConverterTools(
            strategy_decoder=self.mock_decoder,
            runner=self.mock_runner
        )

        class MockConverterTool(ConverterTool):
            def __init__(self, input_format, output_format, input_semantic_format="", output_semantic_format=""):
                self.prob_true = 1
                self.cost_api = 1
                self.input_format = input_format
                self._output_format = output_format
                self.input_semantic_format = input_semantic_format
                self._output_semantic_format = output_semantic_format

            def clone(self):
                return MockConverterTool(
                    self.input_format, self.output_format, self.input_semantic_format, self.output_semantic_format
                )

            # Переопределяет абстрактные методы
            def calc_loss(self, input_data, output_data):
                return 0

            def processing(self, input_data):
                return input_data

        self.MockConverterTool = MockConverterTool

    def test_get_strategy_valid(self):

        tools = [
            self.MockConverterTool("A", "B"),
            self.MockConverterTool("B", "C"),
            self.MockConverterTool("C", "D")
        ]

        class MockEdgeWithToolConverter(EdgeWithToolConverter):
            def __init__(self, start, end, tool):
                self.start = start
                self.end = end
                self.tools = [tool]

            def add_tool(self, tool):
                self.tools.append(tool)

            def calc_weight(self):
                pass

        mock_graph = MagicMock(spec=GraphW)
        mock_dijkstra = MagicMock(spec=DijkstraSPath)
        mock_spt = MagicMock(spec=ShortestPathTree)

        DijkstraSPath.return_value = mock_dijkstra
        mock_dijkstra.edges = []
        mock_dijkstra.distances = []
        mock_spt.get_path.return_value = [MockEdgeWithToolConverter(0, 1, tools[0]), MockEdgeWithToolConverter(1, 2, tools[1])]

        self.mock_decoder.get_tools.return_value = tools

        strategy = self.manager.get_strategy("A", "C", tools)

        self.assertIsNotNone(strategy)
        self.assertEqual(len(strategy), 2)
        self.assertEqual(strategy[0][0].input_format, "A")
        self.assertEqual(strategy[0][0].output_format, "B")
        self.assertEqual(strategy[1][0].input_format, "B")
        self.assertEqual(strategy[1][0].output_format, "C")

    def test_get_strategy_no_path(self):
        tools = [
            self.MockConverterTool("A", "B"),
            self.MockConverterTool("C", "D")
        ]

        strategy = self.manager.get_strategy("A", "D", tools)

        self.assertEqual(strategy, [])

    def test_get_strategy_no_exist_path(self):
        tools = [
            self.MockConverterTool("A", "B"),
            self.MockConverterTool("C", "D")
        ]

        strategy = self.manager.get_strategy("A", "E", tools)

        self.assertIsNone(strategy)

    def test_create_and_run(self):
        tools = [
            self.MockConverterTool("A", "B"),
            self.MockConverterTool("B", "C")
        ]
        self.mock_decoder.get_tools.return_value = tools
        self.mock_runner.run.return_value = "result"

        result = self.manager.create_and_run("input_data", "A", "C", tools)

        self.mock_decoder.get_tools.assert_called_once()
        self.mock_runner.run.assert_called_once_with("input_data", tools)
        self.assertEqual(result, "result")

    def test_with_any(self):

        tools = [
            self.MockConverterTool("_Any", "B"),
            self.MockConverterTool("A", "*")
        ]

        result = self.manager._with_any(tools)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].input_format, "A")
        self.assertEqual(result[0].output_format, "*")