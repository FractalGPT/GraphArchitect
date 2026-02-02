# Руководство по туториалам GraphArchitect

Полное руководство по использованию обучающих материалов.

---

## Созданные туториалы

### Статистика

- **Всего туториалов**: 21
- **Уровней сложности**: 3 (Beginner, Intermediate, Advanced)
- **Готовых workflows**: 6
- **Общее время**: ~575 минут (~10 часов)
- **Практических примеров**: 50+

---

## Структура

```
tutorials/
├── README.md                    # Основной обзор
├── INDEX.md                     # Полный индекс туториалов
├── TUTORIAL_GUIDE.md           # Это руководство
│
├── beginner/                    # Начальный уровень (75 мин)
│   ├── 01_quick_start.md       # 5 мин
│   ├── 02_basic_concepts.md    # 15 мин
│   ├── 03_first_workflow.md    # 20 мин
│   ├── 04_understanding_tools.md  # 20 мин
│   └── 05_simple_api_usage.md  # 15 мин
│
├── intermediate/                # Средний уровень (150 мин)
│   ├── 01_graph_algorithms.md  # 30 мин
│   ├── 02_tool_selection.md    # 30 мин
│   ├── 03_nli_parsing.md       # 30 мин
│   ├── 04_training_system.md   # 30 мин
│   └── 05_custom_tools.md      # 30 мин
│
├── advanced/                    # Продвинутый (200 мин)
│   ├── 01_embedding_systems.md # 45 мин
│   ├── 02_custom_algorithms.md # 40 мин
│   ├── 03_production_deployment.md  # 50 мин
│   ├── 04_performance_tuning.md     # 35 мин
│   └── 05_extending_system.md  # 30 мин
│
└── workflows/                   # Готовые сценарии (150 мин)
    ├── customer_support.md     # 30 мин
    ├── content_creation.md     # 25 мин
    ├── data_analysis.md        # 25 мин
    ├── code_review.md          # 25 мин
    ├── research_workflow.md    # 25 мин
    └── document_processing.md  # 20 мин
```

---

## Программы обучения

### Программа 1: Быстрое освоение (2-3 часа)

**Цель**: Научиться использовать готовые workflow

**План**:
```
Час 1:
├─ Quick Start (5 мин)
├─ Basic Concepts (15 мин)
├─ First Workflow (20 мин)
└─ Understanding Tools (20 мин)

Час 2-3:
├─ Customer Support Workflow (30 мин)
├─ Content Creation Workflow (25 мин)
└─ Data Analysis Workflow (25 мин)
```

**Результат**: Умение решать типовые задачи

### Программа 2: Глубокое понимание (1 неделя)

**Цель**: Понимание внутренних механизмов

**План**:
```
День 1-2: Beginner
  - Все 5 туториалов
  - Практические упражнения

День 3-5: Intermediate
  - Graph Algorithms
  - Tool Selection
  - NLI Parsing
  - Training System

День 6-7: Workflows
  - Все 6 сценариев
  - Адаптация под свои задачи
```

**Результат**: Создание собственных решений

### Программа 3: Экспертное владение (2 недели)

**Цель**: Production развертывание и оптимизация

**План**:
```
Неделя 1:
  - Beginner (все)
  - Intermediate (все)
  - Workflows (все)

Неделя 2:
  - Advanced (все)
  - Production deployment
  - Performance tuning
  - Custom extensions
```

**Результат**: Полное владение системой

---

## Как работать с туториалами

### Формат каждого туториала

1. **Заголовок**
   - Уровень сложности
   - Время выполнения
   - Цель обучения

2. **Что вы узнаете**
   - Список ключевых концепций

3. **Теория**
   - Объяснение концепций
   - Примеры и диаграммы

4. **Практика**
   - Рабочий код
   - Пошаговые инструкции

5. **Упражнения**
   - Задания для закрепления
   - Вопросы для самопроверки

6. **Итоги**
   - Краткая сводка
   - Ссылка на следующий туториал

### Рекомендации

- **Последовательность**: Начинайте с beginner, даже если опытны
- **Практика**: Выполняйте все упражнения
- **Эксперименты**: Пробуйте изменять параметры
- **Заметки**: Записывайте ключевые инсайты

---

## Prerequisites

### Для Beginner

- Python 3.8+
- Базовое понимание командной строки
- Умение запускать Python скрипты

### Для Intermediate

- Опыт программирования на Python
- Понимание ООП
- Базовые знания ML концепций (желательно)

### Для Advanced

- Опыт с production системами
- Понимание ML алгоритмов
- Опыт с Docker/deployment
- Знание оптимизации производительности

---

## Практические примеры

### Где находятся

1. **В туториалах**: Встроенные примеры кода
2. **examples/Python/**: Standalone примеры
3. **examples/Python/nli/**: Примеры NLI
4. **src/Web/**: Примеры интеграции

### Как запускать

```bash
# Примеры NLI
cd examples/Python/nli
python example_01_basic_nli.py

# Web API примеры
cd src/GraphArchitectLib/Web
python example_grapharchitect_usage.py
```

---

## Типовые задачи (Use Cases)

### Customer Support

**Туториал**: [workflows/customer_support.md](workflows/customer_support.md)

**Задача**: Автоматическая обработка запросов

**Шаги**: Классификация → Ответ → QA

**Применение**: Email, чат-боты, тикет-системы

### Content Creation

**Туториал**: [workflows/content_creation.md](workflows/content_creation.md)

**Задача**: Создание статей и контента

**Шаги**: Research → Outline → Write → Style → QA

**Применение**: Блоги, маркетинг, SEO

### Data Analysis

**Туториал**: [workflows/data_analysis.md](workflows/data_analysis.md)

**Задача**: Анализ данных и отчеты

**Шаги**: Parse → Analyze → Insights → Report

**Применение**: Бизнес-аналитика, отчеты

### Code Review

**Туториал**: [workflows/code_review.md](workflows/code_review.md)

**Задача**: Автоматическое ревью кода

**Шаги**: Parse → Style → Bugs → Security → Suggestions

**Применение**: CI/CD, pre-commit hooks

### Research

**Туториал**: [workflows/research_workflow.md](workflows/research_workflow.md)

**Задача**: Исследования и обзоры

**Шаги**: Gathering → Analysis → Synthesis → Report

**Применение**: Литературные обзоры, due diligence

### Document Processing

**Туториал**: [workflows/document_processing.md](workflows/document_processing.md)

**Задача**: Обработка документов

**Шаги**: Extract → Analyze → Extract info → Summarize

**Применение**: Контракты, отчеты, архивы

---

## Помощь и поддержка

### Если что-то не работает

1. **Проверьте Prerequisites**
   - Установлен ли Python 3.8+?
   - Запущен ли сервер?
   - Инициализирована ли БД?

2. **Смотрите логи**
   ```bash
   python main.py
   # Логи покажут ошибки
   ```

3. **Запустите диагностику**
   ```bash
   python diagnose.py
   ```

4. **Проверьте API**
   ```bash
   curl http://localhost:8000/api/health
   ```

### Частые вопросы

**Q**: Туториал не работает, ошибка импорта

**A**: Добавьте в PYTHONPATH:
```bash
set PYTHONPATH=C:\...\GraphArchitectLib;%PYTHONPATH%
```

**Q**: Низкая точность NLI

**A**: Используйте Infinity embeddings - см. [advanced/01_embedding_systems.md](advanced/01_embedding_systems.md)

**Q**: Медленно работает

**A**: См. [advanced/04_performance_tuning.md](advanced/04_performance_tuning.md)

---

## Дополнительные ресурсы

### Документация

- `src/Web/README_FINAL.md` - Web API
- `src/grapharchitect/README.md` - Библиотека
- `examples/Python/nli/README.md` - Примеры NLI

### Тесты

- `src/Tests/` - 235 unit тестов
- `src/Web/test_*.py` - Integration тесты

### Конфигурация

- `src/Web/config.py` - Все настройки
- `src/Web/.env.example` - Пример конфигурации

---

## Обратная связь

### Если нашли ошибку

- Проверьте что используете последнюю версию
- Создайте issue с описанием проблемы
- Приложите логи и код

### Предложения по улучшению

Приветствуются предложения:
- Новые туториалы
- Дополнительные примеры
- Улучшения существующих

---

## Итоги

### Что создано

- 21 туториал (575 минут материала)
- 3 уровня сложности
- 6 готовых workflow сценариев
- 50+ практических примеров
- Полная документация

### Покрытие тем

- Базовое использование
- Внутренние механизмы
- Production развертывание
- Типовые сценарии
- Оптимизация и расширение

### Для кого

- Начинающие: Быстрый старт и готовые решения
- Разработчики: Понимание архитектуры
- DevOps: Production настройка
- Data Scientists: ML компоненты

---

**Начните здесь**: [README](README.md) → [Quick Start](beginner/01_quick_start.md)
