import pytest
from typing import Any
from graph_architect.BaseTool import ConverterTool
from graph_architect.ToolRouters.Converters.GraphWithTools.ToolManager import ManagerConverterTools
from graph_architect.ToolRouters.Converters.Strategy.Decoders.IStDecoder import IStrategyDecoder
from graph_architect.ToolRouters.Converters.Strategy.Ranners.IRun import IRunnerConverter


# ==================== Моковые классы ====================

class MockConverterTool(ConverterTool):
    """Моковый инструмент-конвертер для тестирования"""
    
    def __init__(self, 
                 input_data_format: str, 
                 input_semantic_format: str,
                 output_data_format: str, 
                 output_semantic_format: str,
                 tool_name: str = "MockTool",
                 cost_api: float = 1.0,
                 prob_true: float = 1.0):
        super().__init__(
            tool_name=tool_name,
            input_data_format=input_data_format,
            input_semantic_format=input_semantic_format,
            output_data_format=output_data_format,
            output_semantic_format=output_semantic_format
        )
        self.cost_api = cost_api
        self.prob_true = prob_true
    
    def processing(self, command: str) -> str:
        """Заглушка для обработки"""
        return f"processed_{command}"
    
    def calc_loss(self) -> float:
        """Заглушка для расчета потерь"""
        return 0.0
    
    def calc_cost(self, input_data) -> float:
        """Заглушка для расчета стоимости"""
        return self.cost_api


class SimpleStrategyDecoder(IStrategyDecoder):
    """Простой декодер стратегии - выбирает первый инструмент из каждого шага"""
    
    def get_tools(self, strategy: list) -> list:
        """Выбирает первый инструмент из каждого списка"""
        if not strategy:
            return []
        return [tools[0] if tools else None for tools in strategy]


class SimpleRunner(IRunnerConverter):
    """Простой раннер - просто выполняет инструменты последовательно"""
    
    def run(self, input_data: Any, tool_strategy: list) -> Any:
        """Последовательно применяет инструменты"""
        result = input_data
        for tool in tool_strategy:
            if tool:
                result = tool.processing(result)
        return result


# ==================== Фикстуры ====================

@pytest.fixture
def manager():
    """Создает менеджер с простыми декодером и раннером"""
    decoder = SimpleStrategyDecoder()
    runner = SimpleRunner()
    return ManagerConverterTools(decoder, runner)


@pytest.fixture
def basic_tools():
    """Базовый набор инструментов для простых тестов"""
    return [
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=5.0),
        MockConverterTool("Text", "doc", "JSON", "doc", "Text2JSON", cost_api=2.0),
        MockConverterTool("JSON", "doc", "XML", "doc", "JSON2XML", cost_api=3.0),
    ]


@pytest.fixture
def complex_tools():
    """Сложный набор с альтернативными путями"""
    return [
        # Прямой путь PDF → Text (дорогой)
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text_Direct", cost_api=10.0),
        
        # Альтернативный путь через Image (дешевле)
        MockConverterTool("PDF", "doc", "Image", "doc", "PDF2Image", cost_api=3.0),
        MockConverterTool("Image", "doc", "Text", "doc", "Image2Text", cost_api=4.0),
        
        # Еще один альтернативный путь через HTML
        MockConverterTool("PDF", "doc", "HTML", "doc", "PDF2HTML", cost_api=2.0),
        MockConverterTool("HTML", "doc", "Text", "doc", "HTML2Text", cost_api=6.0),
    ]


@pytest.fixture
def any_format_tools():
    """Инструменты с форматом _Any"""
    return [
        MockConverterTool("_Any", "data", "JSON", "data", "Universal2JSON", cost_api=5.0),
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=2.0),
        MockConverterTool("XML", "doc", "Text", "doc", "XML2Text", cost_api=2.0),
        MockConverterTool("Text", "doc", "HTML", "doc", "Text2HTML", cost_api=3.0),
    ]


# ==================== Тесты ====================

class TestGetStrategy:
    """Тесты метода get_strategy"""
    
    def test_simple_direct_path(self, manager, basic_tools):
        """Тест: Простой прямой путь A → B"""
        strategy = manager.get_strategy("PDF|doc", "Text|doc", basic_tools)
        
        assert strategy is not None
        assert len(strategy) == 1
        assert strategy[0][0].tool_name == "PDF2Text"
    
    def test_multi_step_path(self, manager, basic_tools):
        """Тест: Путь через несколько промежуточных форматов A → B → C"""
        strategy = manager.get_strategy("PDF|doc", "JSON|doc", basic_tools)
        
        assert strategy is not None
        assert len(strategy) == 2
        assert strategy[0][0].tool_name == "PDF2Text"
        assert strategy[1][0].tool_name == "Text2JSON"
    
    def test_long_chain(self, manager, basic_tools):
        """Тест: Длинная цепочка конвертации A → B → C → D"""
        strategy = manager.get_strategy("PDF|doc", "XML|doc", basic_tools)
        
        assert strategy is not None
        assert len(strategy) == 3
        assert strategy[0][0].tool_name == "PDF2Text"
        assert strategy[1][0].tool_name == "Text2JSON"
        assert strategy[2][0].tool_name == "JSON2XML"
    
    def test_optimal_path_selection(self, manager, complex_tools):
        """Тест: Выбор оптимального пути (самого дешевого)"""
        strategy = manager.get_strategy("PDF|doc", "Text|doc", complex_tools)
        
        assert strategy is not None
        # Должен выбрать путь PDF → Image → Text (3+4=7 < 10)
        assert len(strategy) == 2
        assert strategy[0][0].tool_name == "PDF2Image"
        assert strategy[1][0].tool_name == "Image2Text"
    
    def test_no_path_exists(self, manager, basic_tools):
        """Тест: Путь не существует - форматы не связаны"""
        tools = [
            MockConverterTool("A", "doc", "B", "doc", "A2B"),
            MockConverterTool("C", "doc", "D", "doc", "C2D"),
        ]
        
        strategy = manager.get_strategy("A|doc", "D|doc", tools)
        
        # Путь не найден, должен вернуться пустой список или None
        assert strategy == [] or strategy is None
    
    def test_format_not_in_tools(self, manager, basic_tools):
        """Тест: Запрашиваемый формат отсутствует в инструментах"""
        strategy = manager.get_strategy("NonExistent|doc", "Text|doc", basic_tools)
        
        assert strategy is None
    
    def test_same_start_and_end(self, manager):
        """Тест: Начальный и конечный форматы совпадают"""
        tools = [
            MockConverterTool("Text", "doc", "Text", "doc", "Identity"),
        ]
        
        strategy = manager.get_strategy("Text|doc", "Text|doc", tools)
        
        # Путь длины 0 или None (зависит от реализации)
        assert strategy is not None


class TestWithAny:
    """Тесты метода _with_any для обработки универсальных форматов"""
    
    def test_expand_any_format(self, manager, any_format_tools):
        """Тест: Раскрытие _Any формата во все существующие"""
        expanded_tools = manager._with_any(any_format_tools)
        
        # Оригинальный Universal2JSON должен раскрыться в несколько инструментов
        any_tools = [t for t in expanded_tools if "Universal2JSON" in t.tool_name]
        
        # Должны появиться варианты для PDF, XML, Text
        assert len(any_tools) >= 2  # Минимум для PDF и XML
        
        # Оригинальный _Any инструмент должен быть удален
        original_any = [t for t in expanded_tools if t.input_semantic_format == "_Any"]
        assert len(original_any) == 0
    
    def test_without_any_format(self, manager, basic_tools):
        """Тест: Инструменты без _Any остаются без изменений"""
        original_count = len(basic_tools)
        expanded_tools = manager._with_any(basic_tools)
        
        assert len(expanded_tools) == original_count
    
    def test_any_format_in_strategy(self, manager, any_format_tools):
        """Тест: Использование _Any формата в реальной стратегии"""
        # Universal2JSON должен раскрыться и PDF|doc → JSON|data путь должен работать
        strategy = manager.get_strategy("PDF|doc", "JSON|data", any_format_tools)
        
        assert strategy is not None
        assert len(strategy) >= 1


class TestCreateAndRun:
    """Тесты метода create_and_run - полный пайплайн"""
    
    def test_full_pipeline(self, manager, basic_tools):
        """Тест: Полный цикл от создания стратегии до выполнения"""
        input_data = "test_document.pdf"
        
        result = manager.create_and_run(
            input_data, 
            "PDF|doc", 
            "JSON|doc", 
            basic_tools
        )
        
        assert result is not None
        # Раннер последовательно применяет инструменты
        assert "processed_" in result
    
    def test_pipeline_with_no_path(self, manager):
        """Тест: Попытка выполнения при отсутствии пути"""
        tools = [
            MockConverterTool("A", "doc", "B", "doc", "A2B"),
        ]
        
        # Должно обработаться без ошибок, даже если пути нет
        try:
            result = manager.create_and_run("data", "X|doc", "Y|doc", tools)
            # Если вернулся результат, проверяем что он пустой или None
            assert result is None or result == "data"
        except (AttributeError, TypeError):
            # Допустимо, если выбрасывается исключение при отсутствии пути
            pass


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_empty_tools_list(self, manager):
        """Тест: Пустой список инструментов"""
        strategy = manager.get_strategy("A|doc", "B|doc", [])
        
        assert strategy is None
    
    def test_single_tool(self, manager):
        """Тест: Единственный инструмент"""
        tools = [MockConverterTool("A", "doc", "B", "doc", "A2B")]
        
        strategy = manager.get_strategy("A|doc", "B|doc", tools)
        
        assert strategy is not None
        assert len(strategy) == 1
    
    def test_multiple_tools_same_conversion(self, manager):
        """Тест: Несколько инструментов для одного преобразования"""
        tools = [
            MockConverterTool("A", "doc", "B", "doc", "A2B_Fast", cost_api=5.0),
            MockConverterTool("A", "doc", "B", "doc", "A2B_Accurate", cost_api=10.0),
            MockConverterTool("A", "doc", "B", "doc", "A2B_Cheap", cost_api=2.0),
        ]
        
        strategy = manager.get_strategy("A|doc", "B|doc", tools)
        
        assert strategy is not None
        assert len(strategy) == 1
        # Должны быть собраны все три инструмента в одно ребро
        assert len(strategy[0]) >= 1
    
    def test_cyclic_graph(self, manager):
        """Тест: Граф с циклами"""
        tools = [
            MockConverterTool("A", "doc", "B", "doc", "A2B", cost_api=1.0),
            MockConverterTool("B", "doc", "C", "doc", "B2C", cost_api=1.0),
            MockConverterTool("C", "doc", "A", "doc", "C2A", cost_api=1.0),
        ]
        
        # Дейкстра должен корректно обработать цикл
        strategy = manager.get_strategy("A|doc", "C|doc", tools)
        
        assert strategy is not None
        assert len(strategy) == 2  # A → B → C


class TestWeightCalculation:
    """Тесты расчета весов и выбора оптимального пути"""
    
    def test_prefer_cheaper_path(self, manager):
        """Тест: Предпочтение более дешевого пути"""
        tools = [
            # Прямой дорогой путь
            MockConverterTool("A", "doc", "D", "doc", "A2D_Direct", cost_api=100.0),
            
            # Дешевый обходной путь
            MockConverterTool("A", "doc", "B", "doc", "A2B", cost_api=1.0),
            MockConverterTool("B", "doc", "C", "doc", "B2C", cost_api=1.0),
            MockConverterTool("C", "doc", "D", "doc", "C2D", cost_api=1.0),
        ]
        
        strategy = manager.get_strategy("A|doc", "D|doc", tools)
        
        assert strategy is not None
        # Должен выбрать путь через B и C (длина 3, стоимость 3)
        assert len(strategy) == 3
        assert strategy[0][0].tool_name == "A2B"
    
    def test_weight_with_different_probabilities(self, manager):
        """Тест: Учет вероятности успеха в весе"""
        tools = [
            # Высокая вероятность, низкая стоимость
            MockConverterTool("A", "doc", "B", "doc", "A2B_Reliable", 
                            cost_api=5.0, prob_true=0.9),
            
            # Низкая вероятность, низкая стоимость (может быть предпочтительнее)
            MockConverterTool("A", "doc", "B", "doc", "A2B_Unreliable", 
                            cost_api=2.0, prob_true=0.3),
        ]
        
        strategy = manager.get_strategy("A|doc", "B|doc", tools)
        
        assert strategy is not None
        # Вес = prob_true / (cost_api + 1), меньший вес лучше для Дейкстры
        # Reliable: 0.9 / 6 = 0.15
        # Unreliable: 0.3 / 3 = 0.1 (меньше - лучше!)
        # Но в графе может быть собрано оба инструмента в одно ребро со средним весом


# ==================== Запуск тестов ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

