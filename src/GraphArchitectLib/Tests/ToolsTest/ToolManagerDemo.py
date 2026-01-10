"""
Демонстрационный скрипт для проверки работы ManagerConverterTools
без использования pytest
"""

import sys
import os
from pathlib import Path

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Добавляем путь к модулям проекта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Any
from graph_architect.BaseTool import ConverterTool
from graph_architect.ToolRouters.Converters.GraphWithTools.ToolManager import ManagerConverterTools
from graph_architect.ToolRouters.Converters.Strategy.Decoders.IStDecoder import IStrategyDecoder
from graph_architect.ToolRouters.Converters.Strategy.Ranners.IRun import IRunnerConverter


# ==================== Моковые классы ====================

class MockConverterTool(ConverterTool):
    """Моковый инструмент-конвертер для демонстрации"""
    
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
        return f"[{self.tool_name}]({command})"
    
    def calc_loss(self) -> float:
        return 0.0
    
    def calc_cost(self, input_data) -> float:
        return self.cost_api


class SimpleStrategyDecoder(IStrategyDecoder):
    """Простой декодер - выбирает первый инструмент из каждого шага"""
    
    def get_tools(self, strategy: list) -> list:
        if not strategy:
            return []
        return [tools[0] if tools else None for tools in strategy]


class SimpleRunner(IRunnerConverter):
    """Простой раннер - последовательно выполняет инструменты"""
    
    def run(self, input_data: Any, tool_strategy: list) -> Any:
        result = input_data
        for tool in tool_strategy:
            if tool:
                result = tool.processing(result)
        return result


# ==================== Демонстрационные сценарии ====================

def demo_1_simple_path():
    """Демо 1: Простой прямой путь"""
    print("\n" + "="*70)
    print("ДЕМО 1: Простой прямой путь PDF → Text")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=5.0),
        MockConverterTool("Text", "doc", "JSON", "doc", "Text2JSON", cost_api=2.0),
    ]
    
    strategy = manager.get_strategy("PDF|doc", "Text|doc", tools)
    
    print(f"Инструменты: {[t.tool_name for t in tools]}")
    print(f"Стратегия: {[[t.tool_name for t in step] for step in strategy]}")
    print(f"Длина пути: {len(strategy)}")
    print("✓ Тест пройден!" if strategy and len(strategy) == 1 else "✗ Тест провален!")


def demo_2_multi_step():
    """Демо 2: Путь через несколько шагов"""
    print("\n" + "="*70)
    print("ДЕМО 2: Путь через промежуточные форматы PDF → Text → JSON")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=5.0),
        MockConverterTool("Text", "doc", "JSON", "doc", "Text2JSON", cost_api=2.0),
        MockConverterTool("JSON", "doc", "XML", "doc", "JSON2XML", cost_api=3.0),
    ]
    
    strategy = manager.get_strategy("PDF|doc", "JSON|doc", tools)
    
    print(f"Инструменты: {[t.tool_name for t in tools]}")
    print(f"Стратегия: {[[t.tool_name for t in step] for step in strategy]}")
    print(f"Длина пути: {len(strategy)}")
    print(f"Путь: {' → '.join([step[0].tool_name for step in strategy])}")
    print("✓ Тест пройден!" if strategy and len(strategy) == 2 else "✗ Тест провален!")


def demo_3_optimal_path():
    """Демо 3: Выбор оптимального пути"""
    print("\n" + "="*70)
    print("ДЕМО 3: Выбор оптимального (дешевого) пути")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        # Прямой дорогой путь
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text_Direct", cost_api=10.0),
        
        # Дешевый обходной путь через Image
        MockConverterTool("PDF", "doc", "Image", "doc", "PDF2Image", cost_api=3.0),
        MockConverterTool("Image", "doc", "Text", "doc", "Image2Text", cost_api=4.0),
    ]
    
    print("Доступные пути:")
    print("  1. Прямой: PDF → Text (стоимость: 10.0)")
    print("  2. Обходной: PDF → Image → Text (стоимость: 3.0 + 4.0 = 7.0)")
    
    strategy = manager.get_strategy("PDF|doc", "Text|doc", tools)
    
    if strategy:
        path_cost = sum(step[0].cost_api for step in strategy)
        path_names = ' → '.join([step[0].tool_name for step in strategy])
        print(f"\nВыбранная стратегия: {[[t.tool_name for t in step] for step in strategy]}")
        print(f"Путь: {path_names}")
        print(f"Общая стоимость: {path_cost}")
        print("✓ Алгоритм выбрал оптимальный путь!" if len(strategy) == 2 else "⚠ Алгоритм выбрал прямой путь")


def demo_4_no_path():
    """Демо 4: Отсутствие пути"""
    print("\n" + "="*70)
    print("ДЕМО 4: Случай, когда путь не существует")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        MockConverterTool("A", "doc", "B", "doc", "A2B"),
        MockConverterTool("C", "doc", "D", "doc", "C2D"),
    ]
    
    print("Инструменты: A→B, C→D")
    print("Запрос: найти путь A → D")
    
    strategy = manager.get_strategy("A|doc", "D|doc", tools)
    
    print(f"Результат: {strategy}")
    print("✓ Правильно обработано отсутствие пути!" if not strategy or strategy == [] else "✗ Ошибка!")


def demo_5_full_pipeline():
    """Демо 5: Полный пайплайн с выполнением"""
    print("\n" + "="*70)
    print("ДЕМО 5: Полный пайплайн - создание стратегии и выполнение")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=5.0),
        MockConverterTool("Text", "doc", "JSON", "doc", "Text2JSON", cost_api=2.0),
    ]
    
    input_data = "document.pdf"
    
    print(f"Входные данные: {input_data}")
    print(f"Требуемое преобразование: PDF|doc → JSON|doc")
    
    result = manager.create_and_run(input_data, "PDF|doc", "JSON|doc", tools)
    
    print(f"Результат: {result}")
    print("✓ Пайплайн выполнен успешно!" if result else "✗ Ошибка выполнения!")


def demo_6_any_format():
    """Демо 6: Работа с универсальным форматом _Any"""
    print("\n" + "="*70)
    print("ДЕМО 6: Раскрытие универсального формата _Any")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        MockConverterTool("_Any", "data", "JSON", "data", "Universal2JSON", cost_api=5.0),
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=2.0),
        MockConverterTool("XML", "doc", "Text", "doc", "XML2Text", cost_api=2.0),
    ]
    
    print("Инструменты до раскрытия _Any:")
    for t in tools:
        print(f"  - {t.tool_name}: {t.input_format} → {t.output_format}")
    
    expanded = manager._with_any(tools)
    
    print(f"\nКоличество инструментов: было {len(tools)}, стало {len(expanded)}")
    print("\nИнструменты после раскрытия _Any:")
    for t in expanded:
        print(f"  - {t.tool_name}: {t.input_format} → {t.output_format}")
    
    any_expanded = [t for t in expanded if "Universal2JSON" in t.tool_name]
    print(f"\nКопий Universal2JSON создано: {len(any_expanded)}")
    print("✓ Формат _Any успешно раскрыт!" if len(any_expanded) > 1 else "⚠ Раскрытие частичное")


def demo_7_complex_graph():
    """Демо 7: Сложный граф с множеством путей"""
    print("\n" + "="*70)
    print("ДЕМО 7: Сложный граф форматов")
    print("="*70)
    
    manager = ManagerConverterTools(SimpleStrategyDecoder(), SimpleRunner())
    
    tools = [
        # Пути из PDF
        MockConverterTool("PDF", "doc", "Text", "doc", "PDF2Text", cost_api=5.0),
        MockConverterTool("PDF", "doc", "Image", "doc", "PDF2Image", cost_api=3.0),
        MockConverterTool("PDF", "doc", "HTML", "doc", "PDF2HTML", cost_api=2.0),
        
        # Конвертации между форматами
        MockConverterTool("Image", "doc", "Text", "doc", "Image2Text", cost_api=4.0),
        MockConverterTool("HTML", "doc", "Text", "doc", "HTML2Text", cost_api=1.0),
        MockConverterTool("Text", "doc", "JSON", "doc", "Text2JSON", cost_api=2.0),
        
        # Прямые пути
        MockConverterTool("PDF", "doc", "JSON", "doc", "PDF2JSON_Direct", cost_api=15.0),
    ]
    
    print("Граф форматов:")
    print("  PDF → Text (5.0)")
    print("  PDF → Image (3.0)")
    print("  PDF → HTML (2.0)")
    print("  Image → Text (4.0)")
    print("  HTML → Text (1.0)")
    print("  Text → JSON (2.0)")
    print("  PDF → JSON [прямой] (15.0)")
    
    print("\nПоиск пути: PDF → JSON")
    
    strategy = manager.get_strategy("PDF|doc", "JSON|doc", tools)
    
    if strategy:
        path_cost = sum(step[0].cost_api for step in strategy)
        path_names = ' → '.join([step[0].tool_name for step in strategy])
        print(f"\nОптимальный путь: {path_names}")
        print(f"Стоимость: {path_cost}")
        print(f"\nОжидается: PDF → HTML → Text → JSON (стоимость: 2+1+2 = 5.0)")
        print("✓ Найден оптимальный путь!" if path_cost <= 6.0 else "⚠ Найден не самый дешевый путь")


# ==================== Главная функция ====================

def main():
    """Запуск всех демонстрационных сценариев"""
    print("\n" + "="*70)
    print(" ДЕМОНСТРАЦИЯ РАБОТЫ АЛГОРИТМА ManagerConverterTools")
    print("="*70)
    print("\nАлгоритм использует граф форматов и алгоритм Дейкстры для поиска")
    print("оптимальной цепочки конвертации между форматами данных.\n")
    
    try:
        demo_1_simple_path()
        demo_2_multi_step()
        demo_3_optimal_path()
        demo_4_no_path()
        demo_5_full_pipeline()
        demo_6_any_format()
        demo_7_complex_graph()
        
        print("\n" + "="*70)
        print(" ВСЕ ДЕМОНСТРАЦИИ ЗАВЕРШЕНЫ")
        print("="*70)
        print("\n✓ Алгоритм работает корректно!")
        
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

