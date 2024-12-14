from typing import List, Dict, Any, Iterable, Optional, Set

from graph_architect.Algorithms.Graph.SPT.Dijkstra import DijkstraSPath
from graph_architect.Algorithms.Graph.SPT.SPTBase import ShortestPathTree
from graph_architect.Algorithms.Graph.WeightedGraph import GraphW
from graph_architect.Converters.BaseTool import ConverterTool
from graph_architect.Converters.GraphWithTools.EdgeWithTool import EdgeWithToolConverter
from graph_architect.Converters.Strategy.Decoders.IStDecoder import IStrategyDecoder
from graph_architect.Converters.Strategy.Ranners.IRun import IRunnerConverter


class ManagerConverterTools:
    """
    Менеджер инструментов-конвертеров
    """

    def __init__(self, strategy_decoder: IStrategyDecoder, runner: IRunnerConverter):
        self.strategy_decoder = strategy_decoder
        self.runner = runner

    def get_strategy(self, start_format: str, end_format: str, tools: Iterable['ConverterTool']) -> Optional[List[List['ConverterTool']]]:
        """
        Получение стратегии конвертации
        """
        tools_l1 = self._with_any(tools)
        format_vertex: Dict[str, int] = {}
        tools_with_vertex: Dict[str, 'EdgeWithToolConverter'] = {}

        graph = GraphW['EdgeWithToolConverter']()
        strategy = None
        l1: List[List['ConverterTool']] = []  # Список списков инструментов

        k = 0

        for tool in tools_l1:
            start = tool.input_format
            end = tool.output_format

            if start not in format_vertex:
                format_vertex[start] = k
                k += 1
            if end not in format_vertex:
                format_vertex[end] = k
                k += 1

            s = format_vertex[start]
            e = format_vertex[end]
            key_a = f"{s}_{e}"

            if key_a in tools_with_vertex:
                tools_with_vertex[key_a].add_tool(tool)
            else:
                tools_with_vertex[key_a] = EdgeWithToolConverter(s, e, tool)

        if start_format not in format_vertex or end_format not in format_vertex:
            return None

        start_point = format_vertex[start_format]
        target_point = format_vertex[end_format]

        for edge in tools_with_vertex.values():
            edge.calc_weight()
            graph.add_edge(edge)

        strategy = DijkstraSPath(graph, start_point)
        spt = ShortestPathTree(strategy.edges, strategy.distances)
        path_solve = spt.get_path(target_point)

        for item in path_solve:
            l1.append(item.tools)

        return l1

    def create_and_run(self, input_data: Any, start_format: str, end_format: str, tools: Iterable['ConverterTool']) -> Any:
        """
        Создание и запуск стратегии
        """
        strategy = self.get_strategy(start_format, end_format, tools)
        tool_list = self.strategy_decoder.get_tools(strategy)
        return self.runner.run(input_data, tool_list)

    def _with_any(self, tools: Iterable['ConverterTool']) -> List['ConverterTool']:
        """
        Создание фиктивных инструментов для форматов "_Any"
        """
        ret_tools = list(tools)
        semantics: Set[str] = set()
        append_tools: List['ConverterTool'] = []

        for tool in ret_tools:
            if tool.input_semantic_format != "_Any":
                semantics.add(tool.input_semantic_format)
            if tool.output_semantic_format != "*":
                semantics.add(tool.output_semantic_format)

        for tool in ret_tools:
            if tool.input_semantic_format == "_Any":
                clone_tool = tool.clone()
                for sem in semantics:
                    new_tool = clone_tool.clone()
                    new_tool.input_semantic_format = sem
                    append_tools.append(new_tool)

        ret_tools = [tool for tool in ret_tools if tool.input_semantic_format != "_Any"]
        ret_tools.extend(append_tools)

        return ret_tools
