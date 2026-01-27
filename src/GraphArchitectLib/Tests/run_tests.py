#!/usr/bin/env python
"""
Скрипт для удобного запуска тестов GraphArchitect.

Использование:
    python run_tests.py                  # Все тесты
    python run_tests.py --fast           # Быстрые тесты
    python run_tests.py --coverage       # С покрытием
    python run_tests.py --module selection  # Только selection
"""

import sys
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    """Утилита для запуска тестов"""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.project_root = self.tests_dir.parent
    
    def run(self, args):
        """Запуск тестов с опциями"""
        cmd = ["pytest"]
        
        # Базовые опции
        cmd.extend(["-v", "--tb=short"])
        
        # Выбор модуля
        if args.module:
            test_file = self._get_test_file(args.module)
            if test_file:
                cmd.append(str(test_file))
            else:
                print(f"❌ Тестовый файл для модуля '{args.module}' не найден")
                return 1
        else:
            cmd.append(str(self.tests_dir))
        
        # Быстрые тесты (без медленных)
        if args.fast:
            cmd.extend(["-m", "not slow"])
            print("⚡ Режим быстрых тестов (без медленных)")
        
        # Только интеграционные
        if args.integration:
            cmd.extend(["-m", "integration"])
            print("🔗 Только интеграционные тесты")
        
        # Только unit
        if args.unit:
            cmd.extend(["-m", "unit"])
            print("🧩 Только unit тесты")
        
        # Покрытие кода
        if args.coverage:
            cmd.extend([
                "--cov=grapharchitect",
                "--cov-report=html",
                "--cov-report=term-missing"
            ])
            print("📊 С измерением покрытия кода")
        
        # Параллельное выполнение
        if args.parallel:
            cmd.extend(["-n", "auto"])
            print("⚙️ Параллельное выполнение")
        
        # Конкретный тест
        if args.test:
            cmd.append(f"-k {args.test}")
            print(f"🎯 Запуск теста: {args.test}")
        
        # Показывать print
        if args.show_print:
            cmd.append("-s")
        
        # Остановка на первой ошибке
        if args.fail_fast:
            cmd.append("-x")
            print("🛑 Остановка на первой ошибке")
        
        # Verbose режим
        if args.verbose:
            cmd.append("-vv")
        
        # Показать самые медленные тесты
        if args.slowest:
            cmd.append(f"--durations={args.slowest}")
        
        # Запуск
        print("\n" + "="*70)
        print("🧪 ЗАПУСК ТЕСТОВ")
        print("="*70)
        print(f"Команда: {' '.join(cmd)}")
        print("="*70 + "\n")
        
        try:
            result = subprocess.run(cmd, cwd=self.tests_dir)
            return result.returncode
        except KeyboardInterrupt:
            print("\n\n⚠️ Тесты прерваны пользователем")
            return 130
        except Exception as e:
            print(f"\n\n❌ Ошибка при запуске тестов: {e}")
            return 1
    
    def _get_test_file(self, module_name):
        """Получить файл теста по имени модуля"""
        test_files = {
            "graph": "test_graph_algorithms.py",
            "algorithms": "test_graph_algorithms.py",
            "entities": "test_entities.py",
            "selection": "test_selection.py",
            "services": "test_services.py",
            "execution": "test_execution_training.py",
            "training": "test_execution_training.py",
            "nli": "test_nli.py",
        }
        
        filename = test_files.get(module_name.lower())
        if filename:
            return self.tests_dir / filename
        return None
    
    def list_tests(self):
        """Показать список доступных тестов"""
        print("\n📋 ДОСТУПНЫЕ ТЕСТЫ:\n")
        
        test_files = [
            ("test_graph_algorithms.py", "Алгоритмы графа (Dijkstra, A*, Yen, ACO)"),
            ("test_entities.py", "Сущности (BaseTool, Connector, TaskDefinition)"),
            ("test_selection.py", "⭐ Выбор инструментов (Softmax, Температура)"),
            ("test_services.py", "Сервисы (GraphBuilder, Embedding, Feedback)"),
            ("test_execution_training.py", "Выполнение и обучение"),
            ("test_nli.py", "Естественно-языковой интерфейс"),
        ]
        
        for filename, description in test_files:
            filepath = self.tests_dir / filename
            if filepath.exists():
                print(f"  ✓ {filename:30} - {description}")
            else:
                print(f"  ✗ {filename:30} - {description} [НЕ НАЙДЕН]")
        
        print("\n📦 МОДУЛИ ДЛЯ --module:")
        modules = ["graph", "entities", "selection", "services", "execution", "training", "nli"]
        for module in modules:
            print(f"  • {module}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Запуск тестов GraphArchitect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run_tests.py                          # Все тесты
  python run_tests.py --fast                   # Быстрые тесты
  python run_tests.py --coverage               # С покрытием
  python run_tests.py --module selection       # Только selection
  python run_tests.py --test "test_softmax"    # Конкретный тест
  python run_tests.py --parallel               # Параллельно
  python run_tests.py --list                   # Список тестов
        """
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Только быстрые тесты (без медленных)"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Только интеграционные тесты"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Только unit тесты"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Измерить покрытие кода"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Параллельное выполнение (требует pytest-xdist)"
    )
    
    parser.add_argument(
        "--module", "-m",
        type=str,
        help="Запустить тесты для конкретного модуля"
    )
    
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Запустить конкретный тест (по имени)"
    )
    
    parser.add_argument(
        "--show-print", "-s",
        action="store_true",
        help="Показывать print в тестах"
    )
    
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Остановиться на первой ошибке"
    )
    
    parser.add_argument(
        "--verbose", "-vv",
        action="store_true",
        help="Максимально подробный вывод"
    )
    
    parser.add_argument(
        "--slowest",
        type=int,
        metavar="N",
        help="Показать N самых медленных тестов"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Показать список доступных тестов"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list:
        runner.list_tests()
        return 0
    
    return runner.run(args)


if __name__ == "__main__":
    sys.exit(main())
