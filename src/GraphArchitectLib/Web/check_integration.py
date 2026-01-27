#!/usr/bin/env python
"""
Скрипт проверки интеграции GraphArchitect с Web API.

Выполняет:
1. Проверку доступности GraphArchitect
2. Тестирование GraphArchitectBridge
3. Проверку конверсии Agent → BaseTool
4. Тестирование выбора инструментов
5. Проверку поиска стратегий

Использование:
    python check_integration.py
"""

import sys
from pathlib import Path

# Добавляем пути
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))


def check_grapharchitect_available():
    """Проверка 1: Доступность GraphArchitect"""
    print("\n" + "="*70)
    print("1️⃣  ПРОВЕРКА ДОСТУПНОСТИ GRAPHARCHITECT")
    print("="*70)
    
    try:
        import grapharchitect
        print("✅ Модуль grapharchitect импортирован")
        print(f"   Версия: {grapharchitect.__version__}")
        return True
    except ImportError as e:
        print(f"❌ GraphArchitect не доступен: {e}")
        print("\n💡 Решение:")
        print("   1. cd ..")
        print("   2. export PYTHONPATH=$(pwd):$PYTHONPATH")
        print("   3. python Web/check_integration.py")
        return False


def check_bridge():
    """Проверка 2: GraphArchitectBridge"""
    print("\n" + "="*70)
    print("2️⃣  ПРОВЕРКА GRAPHARCHITECT BRIDGE")
    print("="*70)
    
    try:
        from grapharchitect_bridge import get_bridge, is_bridge_available
        
        available = is_bridge_available()
        print(f"Bridge доступен: {available}")
        
        if available:
            bridge = get_bridge()
            print(f"✅ Bridge инициализирован")
            print(f"   Инструментов: {len(bridge.tools)}")
            print(f"   Selector: {bridge.selector.__class__.__name__}")
            print(f"   Orchestrator: {bridge.orchestrator.__class__.__name__}")
            return True
        else:
            print("❌ Bridge не доступен")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при проверке Bridge: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_agent_conversion():
    """Проверка 3: Конверсия Agent → BaseTool"""
    print("\n" + "="*70)
    print("3️⃣  ПРОВЕРКА КОНВЕРСИИ AGENT → BASETOOL")
    print("="*70)
    
    try:
        from grapharchitect_bridge import AgentTool
        from agent_library import get_agent, get_all_agents
        
        # Проверяем конверсию одного агента
        agent = get_agent("agent-classifier-gpt4")
        if not agent:
            print("❌ Агент agent-classifier-gpt4 не найден")
            return False
        
        tool = AgentTool(agent)
        
        print(f"✅ Агент конвертирован:")
        print(f"   Agent: {agent.name} (id={agent.id})")
        print(f"   Tool: {tool.metadata.tool_name}")
        print(f"   Reputation: {tool.metadata.reputation:.3f}")
        print(f"   Input: {tool.input.format}")
        print(f"   Output: {tool.output.format}")
        
        # Проверяем все агенты
        agents = get_all_agents()
        success_count = 0
        
        for agent in agents:
            try:
                tool = AgentTool(agent)
                success_count += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка конверсии {agent.id}: {e}")
        
        print(f"\n✅ Успешно конвертировано: {success_count}/{len(agents)} агентов")
        
        return success_count == len(agents)
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_instrument_selection():
    """Проверка 4: Выбор инструментов через softmax"""
    print("\n" + "="*70)
    print("4️⃣  ПРОВЕРКА ВЫБОРА ИНСТРУМЕНТОВ (SOFTMAX)")
    print("="*70)
    
    try:
        from grapharchitect_bridge import get_bridge
        
        bridge = get_bridge()
        
        # Берем группу инструментов
        tools = bridge.tools[:5]
        
        print(f"Кандидаты ({len(tools)}):")
        for tool in tools:
            print(f"   • {tool.metadata.tool_name} (rep={tool.metadata.reputation:.3f})")
        
        # Выбор через softmax
        result = bridge.selector.select_instrument(
            tools,
            task_embedding=None,
            top_k=5
        )
        
        print(f"\n✅ Выбор выполнен:")
        print(f"   Победитель: {result.selected_tool.metadata.tool_name}")
        print(f"   Вероятность: {result.selection_probability:.3f}")
        print(f"   Температура: {result.temperature:.3f}")
        print(f"   Top-K: {result.top_k}")
        
        print(f"\nРаспределение вероятностей:")
        for tool, prob in sorted(
            result.all_probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            logit = result.all_logits[tool]
            print(f"   • {tool.metadata.tool_name:30} p={prob:.3f} logit={logit:.3f}")
        
        # Проверка корректности softmax
        total_prob = sum(result.all_probabilities.values())
        print(f"\nСумма вероятностей: {total_prob:.6f} (должна быть 1.0)")
        
        if abs(total_prob - 1.0) < 1e-6:
            print("✅ Softmax корректен")
            return True
        else:
            print("❌ Ошибка в softmax!")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_strategy_search():
    """Проверка 5: Поиск стратегий в графе"""
    print("\n" + "="*70)
    print("5️⃣  ПРОВЕРКА ПОИСКА СТРАТЕГИЙ В ГРАФЕ")
    print("="*70)
    
    try:
        from grapharchitect_bridge import get_bridge
        import asyncio
        
        bridge = get_bridge()
        
        # Тестовые форматы
        test_cases = [
            ("text|question", "text|category", "Классификация"),
            ("text|outline", "text|content", "Генерация контента"),
            ("text|draft", "text|polished", "Редактирование"),
        ]
        
        for start_fmt, end_fmt, description in test_cases:
            print(f"\n📊 {description}: {start_fmt} → {end_fmt}")
            
            strategies = asyncio.run(bridge.find_strategies(
                start_fmt,
                end_fmt,
                algorithm="dijkstra"
            ))
            
            if strategies:
                print(f"   ✅ Найдено стратегий: {len(strategies)}")
                print(f"   Длина первой: {len(strategies[0])} шагов")
                
                # Показываем первую стратегию
                strategy = strategies[0]
                path = " → ".join([t.metadata.tool_name for t in strategy])
                print(f"   Путь: {path}")
            else:
                print(f"   ⚠️ Стратегии не найдены (нет подходящего пути)")
        
        return True
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_nli():
    """Проверка 6: NLI датасет"""
    print("\n" + "="*70)
    print("6️⃣  ПРОВЕРКА NLI ДАТАСЕТА")
    print("="*70)
    
    try:
        import json
        nli_file = Path(__file__).parent / "data" / "nli_examples.json"
        
        if nli_file.exists():
            with open(nli_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
            
            print(f"✅ NLI датасет найден: {nli_file}")
            print(f"   Примеров: {len(examples)}")
            
            # Показываем несколько примеров
            print(f"\nПримеры:")
            for i, ex in enumerate(examples[:3]):
                print(f"   {i+1}. {ex['task_text'][:60]}...")
            
            return True
        else:
            print(f"⚠️ NLI датасет не найден: {nli_file}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_training_service():
    """Проверка 7: Training Service"""
    print("\n" + "="*70)
    print("7️⃣  ПРОВЕРКА TRAINING SERVICE")
    print("="*70)
    
    try:
        from training_service import get_training_service
        
        service = get_training_service()
        
        print(f"✅ TrainingService инициализирован")
        print(f"   Enabled: {service.enabled}")
        
        if service.enabled:
            import asyncio
            stats = asyncio.run(service.get_statistics())
            
            print(f"\nСтатистика обучения:")
            print(f"   Total executions: {stats.get('total_executions', 0)}")
            print(f"   Average quality: {stats.get('average_quality', 0):.3f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_checks():
    """Запустить все проверки"""
    print("\n" + "="*70)
    print("🔍 ПРОВЕРКА ИНТЕГРАЦИИ GRAPHARCHITECT С WEB API")
    print("="*70)
    print("\nЭтот скрипт проверит все компоненты интеграции.\n")
    
    results = []
    
    # Запускаем проверки
    results.append(("GraphArchitect доступность", check_grapharchitect_available()))
    
    if results[0][1]:  # Если GraphArchitect доступен
        results.append(("GraphArchitectBridge", check_bridge()))
        results.append(("Agent → BaseTool конверсия", check_agent_conversion()))
        results.append(("InstrumentSelector (softmax)", check_instrument_selection()))
        results.append(("Поиск стратегий", check_strategy_search()))
        results.append(("NLI датасет", check_nli()))
        results.append(("TrainingService", check_training_service()))
    
    # Итоговый отчет
    print("\n" + "="*70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*70)
    
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("\n" + "="*70)
    
    if passed_count == total_count:
        print(f"🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ({passed_count}/{total_count})")
        print("="*70)
        print("\n✅ Интеграция работает корректно!")
        print("\n🚀 Можно запускать сервер: python main.py")
        return 0
    else:
        print(f"⚠️ ПРОЙДЕНО: {passed_count}/{total_count}")
        print("="*70)
        print("\n❌ Некоторые проверки не прошли")
        print("\n💡 Смотрите логи выше для деталей")
        return 1


if __name__ == "__main__":
    exit_code = run_all_checks()
    sys.exit(exit_code)
