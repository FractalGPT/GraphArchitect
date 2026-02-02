"""
Датасет тестовых задач для сравнительного анализа.

50 задач различной сложности для проверки:
- Количества решаемых задач
- Качества решений (RLAIF оценка)
- Адаптивности системы
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestTask:
    """Тестовая задача."""
    
    task_id: str
    description: str
    category: str
    complexity: str  # simple, medium, hard
    expected_steps: int  # Ожидаемое количество шагов
    
    # Для проверки правильности
    expected_keywords: List[str]  # Ключевые слова в ответе
    
    # Метаданные
    requires_tools: List[str]  # Типы необходимых инструментов
    can_solve_sequential: bool  # Можно ли решить последовательно


class TestDataset:
    """Датасет тестовых задач."""
    
    @staticmethod
    def get_all_tasks() -> List[TestTask]:
        """Получить все 50 тестовых задач."""
        
        tasks = []
        
        # ========== ПРОСТЫЕ ЗАДАЧИ (1 шаг) ==========
        
        # 1-10: Классификация
        for i in range(1, 6):
            tasks.append(TestTask(
                task_id=f"classify_{i}",
                description=f"Классифицировать текст: '{_get_sample_text(i)}'",
                category="classification",
                complexity="simple",
                expected_steps=1,
                expected_keywords=["категория", "классификация"],
                requires_tools=["classifier"],
                can_solve_sequential=True
            ))
        
        # 6-10: QA
        for i in range(1, 6):
            tasks.append(TestTask(
                task_id=f"qa_{i}",
                description=f"Ответить на вопрос: {_get_sample_question(i)}",
                category="qa",
                complexity="simple",
                expected_steps=1,
                expected_keywords=["ответ"],
                requires_tools=["qa"],
                can_solve_sequential=True
            ))
        
        # ========== СРЕДНИЕ ЗАДАЧИ (2-3 шага) ==========
        
        # 11-20: Создание контента
        for i in range(1, 11):
            tasks.append(TestTask(
                task_id=f"content_{i}",
                description=f"Создать статью на тему: {_get_topic(i)}",
                category="content_creation",
                complexity="medium",
                expected_steps=2,  # Outline → Write
                expected_keywords=["статья", "текст"],
                requires_tools=["outliner", "writer"],
                can_solve_sequential=True
            ))
        
        # 21-30: Анализ данных
        for i in range(1, 11):
            tasks.append(TestTask(
                task_id=f"analysis_{i}",
                description=f"Проанализировать данные и создать отчет: {_get_data(i)}",
                category="data_analysis",
                complexity="medium",
                expected_steps=2,  # Analyze → Report
                expected_keywords=["анализ", "отчет"],
                requires_tools=["analyzer", "reporter"],
                can_solve_sequential=True
            ))
        
        # ========== СЛОЖНЫЕ ЗАДАЧИ (3+ шагов) ==========
        
        # 31-40: Многошаговая обработка
        for i in range(1, 11):
            tasks.append(TestTask(
                task_id=f"complex_{i}",
                description=f"Исследовать тему '{_get_topic(i)}', создать план, написать статью и проверить качество",
                category="complex_workflow",
                complexity="hard",
                expected_steps=4,  # Research → Outline → Write → QA
                expected_keywords=["исследование", "план", "статья", "проверка"],
                requires_tools=["researcher", "outliner", "writer", "qa"],
                can_solve_sequential=True
            ))
        
        # ========== ГРАФ-СПЕЦИФИЧНЫЕ ЗАДАЧИ (требуют граф) ==========
        
        # 41-50: Задачи с альтернативными путями
        for i in range(1, 11):
            tasks.append(TestTask(
                task_id=f"graph_{i}",
                description=f"Обработать запрос клиента: '{_get_customer_request(i)}' - определить тип, ответить и проверить",
                category="graph_specific",
                complexity="hard",
                expected_steps=3,
                expected_keywords=["тип", "ответ", "проверка"],
                requires_tools=["classifier", "responder", "qa"],
                can_solve_sequential=False  # Требует выбор из альтернатив
            ))
        
        return tasks
    
    @staticmethod
    def get_simple_tasks() -> List[TestTask]:
        """Получить только простые задачи."""
        return [t for t in TestDataset.get_all_tasks() if t.complexity == "simple"]
    
    @staticmethod
    def get_medium_tasks() -> List[TestTask]:
        """Получить задачи средней сложности."""
        return [t for t in TestDataset.get_all_tasks() if t.complexity == "medium"]
    
    @staticmethod
    def get_hard_tasks() -> List[TestTask]:
        """Получить сложные задачи."""
        return [t for t in TestDataset.get_all_tasks() if t.complexity == "hard"]
    
    @staticmethod
    def get_graph_specific_tasks() -> List[TestTask]:
        """Получить задачи, требующие граф-планирования."""
        return [t for t in TestDataset.get_all_tasks() if not t.can_solve_sequential]


# Вспомогательные функции для генерации контента

def _get_sample_text(i: int) -> str:
    """Примеры текстов для классификации."""
    texts = [
        "Отличный продукт, рекомендую!",
        "Ужасное качество, деньги на ветер",
        "Нормально, но могло быть лучше",
        "Не работает как обещано, верну деньги",
        "Превосходное качество, лучшая покупка"
    ]
    return texts[(i - 1) % len(texts)]


def _get_sample_question(i: int) -> str:
    """Примеры вопросов."""
    questions = [
        "Что такое машинное обучение?",
        "Как работает нейронная сеть?",
        "В чем разница между AI и ML?",
        "Что такое deep learning?",
        "Как обучаются языковые модели?"
    ]
    return questions[(i - 1) % len(questions)]


def _get_topic(i: int) -> str:
    """Темы для статей."""
    topics = [
        "Искусственный интеллект в медицине",
        "Блокчейн технологии",
        "Квантовые вычисления",
        "IoT и умные города",
        "Кибербезопасность",
        "Облачные вычисления",
        "Машинное обучение в финансах",
        "Робототехника",
        "Big Data аналитика",
        "5G технологии"
    ]
    return topics[(i - 1) % len(topics)]


def _get_data(i: int) -> str:
    """Данные для анализа."""
    data_samples = [
        "Продажи Q1: 100, Q2: 150, Q3: 180, Q4: 220",
        "Пользователи: январь 1000, февраль 1200, март 1500",
        "Конверсия: день1 5%, день2 7%, день3 6%, день4 8%",
        "Трафик: понедельник 500, вторник 600, среда 550",
        "Регистрации: неделя1 50, неделя2 75, неделя3 90",
        "Отток: месяц1 10%, месяц2 8%, месяц3 12%",
        "Revenue: $10k, $12k, $15k, $18k по месяцам",
        "Активность: утро 30%, день 50%, вечер 20%",
        "Возраст: 18-25 (40%), 26-35 (35%), 36+ (25%)",
        "География: Москва 50%, СПб 30%, другие 20%"
    ]
    return data_samples[(i - 1) % len(data_samples)]


def _get_customer_request(i: int) -> str:
    """Запросы клиентов."""
    requests = [
        "Жду доставку неделю, где заказ?",
        "Как изменить адрес доставки?",
        "Товар пришел поврежденным",
        "Хочу вернуть деньги",
        "Когда будет следующая акция?",
        "Не могу войти в аккаунт",
        "Как отменить подписку?",
        "Почему списали деньги дважды?",
        "Товар не соответствует описанию",
        "Отличный сервис, спасибо!"
    ]
    return requests[(i - 1) % len(requests)]


if __name__ == "__main__":
    # Вывод статистики датасета
    dataset = TestDataset()
    all_tasks = dataset.get_all_tasks()
    
    print("=" * 70)
    print("ДАТАСЕТ ТЕСТОВЫХ ЗАДАЧ")
    print("=" * 70)
    print()
    
    print(f"Всего задач: {len(all_tasks)}")
    print()
    
    # По категориям
    categories = {}
    for task in all_tasks:
        categories[task.category] = categories.get(task.category, 0) + 1
    
    print("По категориям:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:25} {count} задач")
    
    print()
    
    # По сложности
    complexities = {}
    for task in all_tasks:
        complexities[task.complexity] = complexities.get(task.complexity, 0) + 1
    
    print("По сложности:")
    for comp, count in sorted(complexities.items()):
        print(f"  {comp:25} {count} задач")
    
    print()
    
    # Требующие граф
    graph_required = sum(1 for t in all_tasks if not t.can_solve_sequential)
    print(f"Требуют граф-планирования: {graph_required} задач")
    print(f"Можно решить последовательно: {len(all_tasks) - graph_required} задач")
    
    print()
    print("=" * 70)
