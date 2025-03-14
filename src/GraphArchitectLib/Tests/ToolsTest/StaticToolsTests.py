import pytest
from typing import Any

from graph_architect.BaseTool import StaticTool
from graph_architect.BaseTool import BaseIntTool

@pytest.fixture
def clear_static_objects():
    """Фикстура для очистки статического словаря перед каждым тестом."""
    StaticTool.objects.clear()

def test_initialization(clear_static_objects):
    """
    Проверка, что все свойства корректно инициализируются.
    """

    def mock_kernel(x: Any) -> Any:
        return x * 2

    tool = StaticTool("int", "_Any", "int", "*", "DoubleIt", mock_kernel)

    assert tool.input_data_format == "int"
    assert tool.input_semantic_format == "_Any"
    assert tool.output_data_format == "int"
    assert tool.output_semantic_format == "*"
    assert tool.tool_name == "DoubleIt"
    assert tool.tool_id == 0


def test_processing(clear_static_objects):
    """
    Проверка, что метод processing корректно обрабатывает команду и добавляет результат в статический словарь.
    """

    def mock_kernel(x: int) -> int:
        return x * 2

    tool = StaticTool("int", "_Any", "int", "*", "DoubleIt", mock_kernel)
    StaticTool.add_object("obj1", 5)

    result = tool.processing("obj1")

    assert result == "DoubleIt_int|_Any_int|_Any_0"
    assert StaticTool.objects["DoubleIt_int|_Any_int|_Any_0"] == 10


def test_calc_loss(clear_static_objects):
    """
    Проверка, что метод calc_loss возвращает ожидаемое значение.
    """

    def mock_kernel(x: Any) -> Any:
        return x

    tool = StaticTool("int", "_Any", "int", "*", "Identity", mock_kernel)

    assert tool.calc_loss() == 0.0


def test_static_objects(clear_static_objects):
    """
    Проверка, что статический словарь корректно работает и хранит объекты.
    """

    def mock_kernel(x: Any) -> Any:
        return x

    tool1 = StaticTool("int", "_Any", "int", "*", "Tool1", mock_kernel)
    tool2 = StaticTool("str", "_Any", "str", "*", "Tool2", mock_kernel)

    StaticTool.add_object("obj1", 5)
    StaticTool.add_object("obj2", "Привет")

    assert "obj1" in StaticTool.objects
    assert "obj2" in StaticTool.objects
    assert StaticTool.objects["obj1"] == 5
    assert StaticTool.objects["obj2"] == "Привет"

    result1 = tool1.processing("obj1")
    result2 = tool2.processing("obj2")

    assert result1 in StaticTool.objects
    assert result2 in StaticTool.objects
    assert StaticTool.objects[result1] == 5
    assert StaticTool.objects[result2] == "Привет"