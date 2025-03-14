import pytest
from unittest.mock import MagicMock

from graph_architect.BaseTool import ConverterTool
from graph_architect.ToolRouters.Converters.GraphWithTools.EdgeWithTool import EdgeWithToolConverter
from graph_architect.ToolRouters.Converters.GraphWithTools.ToolManager import ManagerConverterTools
from graph_architect.ToolRouters.Converters.Strategy.Decoders.IStDecoder import IStrategyDecoder
from graph_architect.ToolRouters.Converters.Strategy.Ranners.IRun import IRunnerConverter
from graph_architect.Algorithms.Graph.SPT.Dijkstra import DijkstraSPath
from graph_architect.Algorithms.Graph.SPT.SPTBase import ShortestPathTree
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW

# Мок классов
@pytest.fixture
def mock_manager():
    mock_decoder = MagicMock(spec=IStrategyDecoder)
    mock_runner = MagicMock(spec=IRunnerConverter)

    # Создаем экземпляр ManagerConverterTools
    manager = ManagerConverterTools(
        strategy_decoder=mock_decoder,
        runner=mock_runner
    )

    # Мок конвертера
    class MockConverterTool(ConverterTool):
        def __init__(self, input_format, output_format, input_semantic_format="", output_semantic_format=""):
            self.prob_true = 1
            self.cost_api = 1
            #self.input_data_format = input_format
            self.input_format = input_format
            self._output_format = output_format
            self.input_semantic_format = input_semantic_format
            self._output_semantic_format = output_semantic_format

        def clone(self):
            return MockConverterTool(
                self.input_format, self.output_format, self.input_semantic_format, self.output_semantic_format
            )

        # Переопределяет абстрактные методы
        def calc_loss(self):
            return 0.0

        # Переопределяет абстрактные методы
        def calc_cost(self, input_data):
            return 0

        def processing(self, command: str) -> None:
            return

        #def processing(self, command: str) -> str:
        #    inp = self.objects[command]
        #    outp = self._kernel(inp)
        #    new_name = f"{self.tool_name}_{self.input_format}_{self.output_format}_{self.tool_id}"
        #    self.objects[new_name] = outp
        #    return new_name

    return manager, MockConverterTool


def test_get_strategy_valid(mock_manager):
    manager, MockConverterTool = mock_manager

    tools = [
        MockConverterTool("A", "B"),
        MockConverterTool("B", "C"),
        MockConverterTool("C", "D")
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

    #mock_graph = MagicMock(spec=GraphW)
    mock_dijkstra = MagicMock(spec=DijkstraSPath)
    mock_spt = MagicMock(spec=ShortestPathTree)

    DijkstraSPath.return_value = mock_dijkstra
    mock_dijkstra.edges = []
    mock_dijkstra.distances = []
    mock_spt.get_path.return_value = [MockEdgeWithToolConverter(0, 1, tools[0]), MockEdgeWithToolConverter(1, 2, tools[1])]

    manager.strategy_decoder.get_tools.return_value = tools

    strategy = manager.get_strategy("A", "C", tools)

    assert strategy is not None
    assert len(strategy) == 2
    assert strategy[0][0].input_format == "A"
    assert strategy[0][0].output_format == "B"
    assert strategy[1][0].input_format == "B"
    assert strategy[1][0].output_format == "C"


def test_get_strategy_no_path(mock_manager):
    manager, MockConverterTool = mock_manager

    tools = [
        MockConverterTool("A", "B"),
        MockConverterTool("C", "D")
    ]

    strategy = manager.get_strategy("A", "D", tools)

    assert strategy == []


def test_get_strategy_no_exist_path(mock_manager):
    manager, MockConverterTool = mock_manager

    tools = [
        MockConverterTool("A", "B"),
        MockConverterTool("C", "D")
    ]

    strategy = manager.get_strategy("A", "E", tools)

    assert strategy is None


def test_create_and_run(mock_manager):
    manager, MockConverterTool = mock_manager

    tools = [
        MockConverterTool("A", "B"),
        MockConverterTool("B", "C")
    ]
    manager.strategy_decoder.get_tools.return_value = tools
    manager.runner.run.return_value = "result"

    result = manager.create_and_run("input_data", "A", "C", tools)

    manager.strategy_decoder.get_tools.assert_called_once()
    manager.runner.run.assert_called_once_with("input_data", tools)
    assert result == "result"


def test_with_any(mock_manager):
    manager, MockConverterTool = mock_manager

    tools = [
        MockConverterTool("_Any", "B"),
        MockConverterTool("A", "*")
    ]

    result = manager._with_any(tools)

    assert len(result) == 1
    assert result[0].input_format == "A"
    assert result[0].output_format == "*"