from typing import Callable, Dict, Any
from abc import ABC, abstractmethod
from collections.abc import Iterable


class BaseConverterTool(ABC):
    """
    Основной абстрактный класс инструмента
    """
    def __init__(self, tool_id: int = 0, tool_name: str = "", tool_description: str = "",
                 input_data_format: str = "", input_semantic_format: str = "_Any",
                 output_data_format: str = "", output_semantic_format: str = "*"):
        self.tool_id = tool_id
        self._tool_name = tool_name
        self.tool_description = tool_description
        self.input_data_format = input_data_format
        self.input_semantic_format = input_semantic_format
        self._output_data_format = output_data_format
        self._output_semantic_format = output_semantic_format
        self._output_format = self.__get_output_format()
        self.prob_true = 1.0
        self.cost_api = 1.0

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cost(self) -> float:
        """Простая стоимостная функция"""
        #Todo: сделать сложнее и  "умнее"
        return self.prob_true / (self.cost_api + 1)

    @tool_name.setter
    def tool_name(self, value: str):
        raise AttributeError("Cannot modify tool_name directly")

    @property
    def output_data_format(self) -> str:
        return self._output_data_format

    @property
    def output_semantic_format(self) -> str:
        return self._output_semantic_format

    @property
    def output_format(self) -> str:
        return self._output_format

    @output_data_format.setter
    def output_data_format(self, value: str):
        self.output_data_format = value
        self._output_format = self.__get_output_format()

    @output_semantic_format.setter
    def output_semantic_format(self, value: str):
        self._output_semantic_format = value
        self._output_format = self.__get_output_format()

    @output_format.setter
    def output_format(self, value: str):
        self._output_format = value

    def __get_output_format(self) -> str:
        """Получить выходной формат"""
        return (f"{self.output_data_format}|{self.output_semantic_format}"
                if self.output_semantic_format != "*"
                else f"{self.output_data_format}|{self.input_semantic_format}")

    @abstractmethod
    def processing(self, command: str):
        pass

    @abstractmethod
    def calc_loss(self) -> float:
        pass

    def clone(self):
        return self.__class__(**self.__dict__)

    @staticmethod
    def filter(tools: Iterable['BaseConverterTool'], max_cost: float = float('inf'), min_probe: float = 0) -> list:
        return [tool for tool in tools if tool.prob_true >= min_probe and tool.cost_api <= max_cost]


class ConverterTool(BaseConverterTool, ABC):
    """
       Абстрактный класс инструмента с расширенным описанием
    """
    def __init__(self, tool_id: int = 0, tool_name: str = "", tool_description: str = "",
                 input_data_format: str = "", input_semantic_format: str = "_Any",
                 output_data_format: str = "", output_semantic_format: str = "*", convert: str = ""):
        super().__init__(tool_id, tool_name, tool_description, input_data_format, input_semantic_format,
                         output_data_format, output_semantic_format)
        self.convert = convert

    @property
    def convert(self) -> str:
        return self._convert

    @convert.setter
    def convert(self, value: str):
        self._convert = value

    def set_convert(self, from_format: str, to_format: str):
        self.convert = f"{from_format}_{to_format}"
        self.input_data_format = from_format
        self.output_data_format = to_format


class StaticTool(ConverterTool):
    '''
    Класс не изменяемого (во время выполлнения программы) инструмента
    '''
    # Статический словарь для хранения объектов
    objects: Dict[str, Any] = {}

    def __init__(self, inp_d: str, inp_sem: str, out_data: str, out_sem: str, name: str, func: Callable[[Any], Any]):
        super().__init__(input_data_format=inp_d, input_semantic_format=inp_sem,
                         output_data_format=out_data, output_semantic_format=out_sem, tool_name=name)
        self._kernel = func

    def processing(self, command: str) -> str:
        inp = self.objects[command]
        outp = self._kernel(inp)
        new_name = f"{self.tool_name}_{self.input_format}_{self.output_format}_{self.tool_id}"
        self.objects[new_name] = outp
        return new_name

    def calc_loss(self) -> float:
        return 0.0

    @staticmethod
    def get_objects() -> Dict[str, Any]:
        return StaticTool.objects

    @staticmethod
    def add_object(name: str, obj: Any):
        StaticTool.objects[name] = obj
