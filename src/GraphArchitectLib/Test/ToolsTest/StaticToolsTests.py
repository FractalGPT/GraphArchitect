import unittest
from typing import Any

from Converters.BaseTool import StaticTool


class TestStaticTool(unittest.TestCase):

    def setUp(self):
        # Очистка статического словаря перед каждым тестом
        StaticTool.objects.clear()

    def test_initialization(self):
        """
        Проверка, что все свойства корректно инициализируются.
        """
        self.setUp()

        # Тест инициализации
        def mock_kernel(x: Any) -> Any:
            return x * 2

        tool = StaticTool("int", "_Any", "int", "*", "DoubleIt", mock_kernel)
        self.assertEqual(tool.input_data_format, "int")
        self.assertEqual(tool.input_semantic_format, "_Any")
        self.assertEqual(tool.output_data_format, "int")
        self.assertEqual(tool.output_semantic_format, "*")
        self.assertEqual(tool.tool_name, "DoubleIt")
        self.assertEqual(tool.tool_id, 0)

    def test_processing(self):
        """
          Проверка, что метод processing корректно обрабатывает команду и добавляет результат в статический словарь.
        """
        self.setUp()

        # Тест обработки команды
        def mock_kernel(x: int) -> int:
            return x * 2

        tool = StaticTool("int", "_Any", "int", "*", "DoubleIt", mock_kernel)
        StaticTool.add_object("obj1", 5)
        result = tool.processing("obj1")
        self.assertEqual(result, "DoubleIt_int|_Any_int|_Any_0")
        self.assertEqual(StaticTool.objects["DoubleIt_int|_Any_int|_Any_0"], 10)

    def test_calc_loss(self):
        """
          Проверка, что метод calc_loss возвращает ожидаемое значение
        """
        self.setUp()

        # Тест метода calc_loss
        def mock_kernel(x: Any) -> Any:
            return x

        tool = StaticTool("int", "_Any", "int", "*", "Identity", mock_kernel)
        self.assertEqual(tool.calc_loss(), 0.0)

    def test_static_objects(self):
        """
          Проверка, что статический словарь корректно работает и хранит объекты
        """
        self.setUp()

        # Тест статического словаря
        def mock_kernel(x: Any) -> Any:
            return x

        tool1 = StaticTool("int", "_Any", "int", "*", "Tool1", mock_kernel)
        tool2 = StaticTool("str", "_Any", "str", "*", "Tool2", mock_kernel)

        StaticTool.add_object("obj1", 5)
        StaticTool.add_object("obj2", "Привет")

        self.assertIn("obj1", StaticTool.objects)
        self.assertIn("obj2", StaticTool.objects)
        self.assertEqual(StaticTool.objects["obj1"], 5)
        self.assertEqual(StaticTool.objects["obj2"], "Привет")

        result1 = tool1.processing("obj1")
        result2 = tool2.processing("obj2")

        self.assertIn(result1, StaticTool.objects)
        self.assertIn(result2, StaticTool.objects)
        self.assertEqual(StaticTool.objects[result1], 5)
        self.assertEqual(StaticTool.objects[result2], "Привет")
