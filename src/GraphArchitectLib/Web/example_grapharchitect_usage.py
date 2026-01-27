"""
Примеры использования Web API с интеграцией GraphArchitect.

Демонстрирует:
- Реальный выбор инструментов через softmax
- Поиск стратегий с разными алгоритмами
- Обучение на основе feedback
- Получение метрик инструментов
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000/api"


def example_1_health_check():
    """Пример 1: Проверка статуса интеграции"""
    print("\n" + "="*70)
    print("ПРИМЕР 1: Проверка интеграции GraphArchitect")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print(f"\nСтатус API: {'✓ Online' if health['success'] else '✗ Offline'}")
    print(f"Версия: {health['data']['version']}")
    
    features = health['data']['features']
    print(f"\nРежим работы:")
    print(f"  GraphArchitect: {'✅ Активирован' if features['real_algorithms'] else '⚠️ Симуляция'}")
    print(f"  Реальные алгоритмы: {'✅ Да' if features['real_algorithms'] else '❌ Нет'}")
    print(f"  Softmax выбор: {'✅ Да' if features['softmax_selection'] else '❌ Нет'}")
    print(f"  Обучение: {'✅ Да' if features['training'] else '❌ Нет'}")
    print(f"  NLI: {'✅ Да' if features['nli'] else '❌ Нет'}")
    
    return features['real_algorithms']


def example_2_streaming_with_real_algorithms():
    """Пример 2: Стриминг с реальными алгоритмами"""
    print("\n" + "="*70)
    print("ПРИМЕР 2: Выполнение задачи с реальными алгоритмами")
    print("="*70)
    
    chat_id = f"demo_{int(time.time())}"
    
    # Тестируем разные алгоритмы
    algorithms = ["dijkstra", "yen_5", "ant_5"]
    
    for algo in algorithms:
        print(f"\n🔍 Алгоритм: {algo}")
        print("-" * 70)
        
        response = requests.post(
            f"{BASE_URL}/chat/{chat_id}/message/stream",
            data={
                "message": "Проанализировать текст и определить его категорию",
                "planning_algorithm": algo
            },
            stream=True
        )
        
        step_count = 0
        selected_agents = []
        temperatures = []
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    
                    if chunk["type"] == "step_started":
                        step_count += 1
                        print(f"\n  Шаг {step_count}: {chunk.get('content', 'N/A')}")
                    
                    elif chunk["type"] == "agent_selected":
                        agent_id = chunk.get("agent_id", "unknown")
                        score = chunk.get("score", 0)
                        temp = chunk.get("metadata", {}).get("temperature", 0)
                        
                        selected_agents.append(agent_id)
                        temperatures.append(temp)
                        
                        print(f"    ✓ Выбран: {agent_id}")
                        print(f"      Вероятность: {score:.3f}")
                        if temp:
                            print(f"      Температура: {temp:.3f}")
                    
                    elif chunk["type"] == "text":
                        print(f"\n  📝 Результат: {chunk.get('content', '')[:100]}...")
                
                except json.JSONDecodeError:
                    pass
        
        print(f"\n  📊 Итого:")
        print(f"    Шагов: {step_count}")
        print(f"    Агентов выбрано: {len(selected_agents)}")
        if temperatures:
            avg_temp = sum(temperatures) / len(temperatures)
            print(f"    Средняя температура: {avg_temp:.3f}")


def example_3_training_metrics():
    """Пример 3: Метрики обучения"""
    print("\n" + "="*70)
    print("ПРИМЕР 3: Метрики обучения инструментов")
    print("="*70)
    
    # Общая статистика
    print("\n📊 Общая статистика обучения:")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/training/statistics")
    stats = response.json()
    
    if stats.get("enabled"):
        print(f"  Всего выполнений: {stats.get('total_executions', 0)}")
        print(f"  Средняя оценка: {stats.get('average_quality', 0):.3f}")
        print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
        print(f"  Среднее время: {stats.get('average_execution_time', 0):.2f}s")
        print(f"  Средняя стоимость: ${stats.get('average_cost', 0):.3f}")
    else:
        print("  ⚠️ Training Service не активен")
    
    # Метрики топ инструментов
    print("\n🏆 Топ-5 инструментов по репутации:")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/training/tools")
    tools_data = response.json()
    
    if tools_data.get("enabled") and tools_data.get("tools"):
        top_tools = tools_data["tools"][:5]
        
        for i, tool in enumerate(top_tools, 1):
            print(f"\n  {i}. {tool['tool_name']}")
            print(f"     Репутация: {tool['reputation']:.3f}")
            print(f"     Обучено на: {tool['training_sample_size']} примерах")
            print(f"     Дисперсия: {tool['variance_estimate']:.3f}")
            print(f"     Стоимость: ${tool['mean_cost']:.3f}")
    else:
        print("  ⚠️ Метрики не доступны")


def example_4_submit_feedback():
    """Пример 4: Отправка обратной связи"""
    print("\n" + "="*70)
    print("ПРИМЕР 4: Обратная связь для обучения")
    print("="*70)
    
    # Генерируем тестовый task_id
    import uuid
    task_id = str(uuid.uuid4())
    
    print(f"\n📝 Отправка обратной связи для задачи: {task_id}")
    
    response = requests.post(
        f"{BASE_URL}/training/feedback",
        data={
            "task_id": task_id,
            "quality_score": 0.92,
            "comment": "Отличный результат, агент справился идеально!"
        }
    )
    
    result = response.json()
    
    if result.get("success"):
        print(f"  ✅ {result.get('message')}")
        print(f"  Оценка сохранена: {result.get('quality_score')}")
    else:
        print(f"  ⚠️ {result.get('message')}")


def example_5_compare_algorithms():
    """Пример 5: Сравнение алгоритмов поиска"""
    print("\n" + "="*70)
    print("ПРИМЕР 5: Сравнение алгоритмов поиска путей")
    print("="*70)
    
    chat_id = f"compare_{int(time.time())}"
    message = "Проанализировать данные, создать отчет и проверить качество"
    
    algorithms = [
        ("dijkstra", "Dijkstra - один лучший путь"),
        ("yen_3", "Yen - топ-3 пути"),
        ("ant_5", "Ant Colony - топ-5 путей")
    ]
    
    for algo, description in algorithms:
        print(f"\n📊 {description}")
        print("-" * 70)
        
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/chat/{chat_id}/message/stream",
            data={
                "message": message,
                "planning_algorithm": algo
            },
            stream=True
        )
        
        strategies_found = 0
        steps_count = 0
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    
                    if chunk["type"] == "gen_phase_complete":
                        metadata = chunk.get("metadata", {})
                        if "strategies_found" in metadata:
                            strategies_found = metadata["strategies_found"]
                    
                    elif chunk["type"] == "step_started":
                        steps_count += 1
                
                except json.JSONDecodeError:
                    pass
        
        elapsed = time.time() - start_time
        
        print(f"  Стратегий найдено: {strategies_found}")
        print(f"  Шагов выполнения: {steps_count}")
        print(f"  Время: {elapsed:.2f}s")


def example_6_tool_metrics():
    """Пример 6: Детальные метрики инструмента"""
    print("\n" + "="*70)
    print("ПРИМЕР 6: Детальные метрики конкретного инструмента")
    print("="*70)
    
    agent_id = "agent-classifier-gpt4"
    
    print(f"\n🔍 Получение метрик для: {agent_id}")
    
    response = requests.get(f"{BASE_URL}/training/tools/{agent_id}")
    
    if response.status_code == 200:
        metrics = response.json()
        
        print(f"\n✅ Метрики инструмента:")
        print(f"  Название: {metrics['tool_name']}")
        print(f"  Репутация: {metrics['reputation']:.3f}")
        print(f"  Стоимость: ${metrics['mean_cost']:.3f}")
        print(f"  Среднее время: {metrics['mean_time']:.2f}s")
        print(f"  Размер выборки: {metrics['training_sample_size']}")
        print(f"  Дисперсия: {metrics['variance_estimate']:.3f}")
        print(f"  История оценок: {metrics['quality_scores_count']} записей")
        print(f"  Эмбеддинг: {'✓ Есть' if metrics['has_embedding'] else '✗ Нет'}")
    else:
        print(f"  ❌ Инструмент не найден (статус {response.status_code})")


def main():
    """Запуск всех примеров"""
    print("\n" + "="*70)
    print(" ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ GRAPHARCHITECT WEB API")
    print("="*70)
    print("\nУбедитесь что сервер запущен: python main.py")
    print("="*70)
    
    try:
        # Проверяем доступность API
        is_grapharchitect = example_1_health_check()
        
        if not is_grapharchitect:
            print("\n⚠️ GraphArchitect работает в режиме симуляции")
            print("Некоторые примеры могут показывать не реальные данные")
            print("\nЗапустите check_integration.py для диагностики")
            
            response = input("\nПродолжить? (y/n): ")
            if response.lower() != 'y':
                return
        
        # Запускаем примеры
        example_2_streaming_with_real_algorithms()
        example_3_training_metrics()
        example_4_submit_feedback()
        example_5_compare_algorithms()
        example_6_tool_metrics()
        
        print("\n" + "="*70)
        print(" ✓ ВСЕ ПРИМЕРЫ ВЫПОЛНЕНЫ УСПЕШНО!")
        print("="*70)
        
        if is_grapharchitect:
            print("\n🎉 GraphArchitect работает в реальном режиме!")
            print("Вы видели реальные алгоритмы, softmax и обучение!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ОШИБКА: Не удается подключиться к API")
        print("Запустите сервер: python main.py")
    except Exception as e:
        print(f"\n✗ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
