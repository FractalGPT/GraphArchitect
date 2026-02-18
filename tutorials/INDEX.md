# GraphArchitect Tutorials - Полный индекс

Навигация по всем туториалам и обучающим материалам.

---

## Быстрый доступ

### Я хочу...

**...быстро начать работу**
→ [Быстрый старт](beginner/01_quick_start.md) (5 минут)

**...понять как это работает**
→ [Основные концепции](beginner/02_basic_concepts.md) (15 минут)

**...создать свой workflow**
→ [Первый Workflow](beginner/03_first_workflow.md) (20 минут)

**...использовать готовый сценарий**
→ [Customer Support](workflows/customer_support.md)
→ [Content Creation](workflows/content_creation.md)
→ [Data Analysis](workflows/data_analysis.md)

**...улучшить качество**
→ [Системы эмбеддингов](deployment/01_embedding_systems.md)

**...понять математику**
→ [Выбор инструментов](intermediate/02_tool_selection.md)

---

## Все туториалы

### Beginner (5 туториалов, 60 минут)

1. **Quick Start** (5 мин)
   - Установка и первый запуск
   - [beginner/01_quick_start.md](beginner/01_quick_start.md)

2. **Basic Concepts** (15 мин)
   - Граф, коннекторы, стратегии
   - [beginner/02_basic_concepts.md](beginner/02_basic_concepts.md)

3. **First Workflow** (20 мин)
   - Создание и выполнение workflow
   - [beginner/03_first_workflow.md](beginner/03_first_workflow.md)

4. **Understanding Tools** (20 мин)
   - Как устроены инструменты
   - [beginner/04_understanding_tools.md](beginner/04_understanding_tools.md)

### Intermediate (2 туториалов, 60 минут)

1. **Graph Algorithms** (30 мин)
   - Dijkstra, A*, Yen, ACO
   - [intermediate/01_graph_algorithms.md](intermediate/01_graph_algorithms.md)

2. **Tool Selection** (30 мин)
   - Softmax, температура, логиты
   - [intermediate/02_tool_selection.md](intermediate/02_tool_selection.md)

### Deployment (2 туториала, 95 минут)

1. **Embedding Systems** (45 мин)
   - Simple, Infinity, Faiss
   - [advanced/01_embedding_systems.md](deployment/01_embedding_systems.md)

2. **Production Deployment** (50 мин)
   - Docker, масштабирование
   - [deployment/02_production_deployment.md](deployment/02_production_deployment.md)

### Workflows (6 готовых сценариев, 150 минут)

1. **Customer Support** (30 мин)
   - Обработка запросов клиентов
   - [workflows/customer_support.md](workflows/customer_support.md)

2. **Content Creation** (25 мин)
   - Автоматическое создание статей
   - [workflows/content_creation.md](workflows/content_creation.md)

3. **Data Analysis** (25 мин)
   - Анализ данных и отчеты
   - [workflows/data_analysis.md](workflows/data_analysis.md)

4. **Code Review** (25 мин)
   - Автоматическое ревью кода
   - [workflows/code_review.md](workflows/code_review.md)

5. **Research Workflow** (25 мин)
   - Исследовательские задачи
   - [workflows/research_workflow.md](workflows/research_workflow.md)

6. **Document Processing** (20 мин)
   - Обработка документов
   - [workflows/document_processing.md](workflows/document_processing.md)

---

## Рекомендуемый порядок изучения

### Путь 1: Быстрое освоение (2 часа)

```
День 1 (2 часа):
├─ Quick Start (5 мин)
├─ Basic Concepts (15 мин)
├─ First Workflow (20 мин)
├─ Customer Support Workflow (30 мин)
└─ Content Creation Workflow (25 мин)
```

**Результат**: Умение использовать готовые workflow

### Путь 2: Глубокое понимание (1 неделя)

```
День 1-2: Beginner (все 5)
День 3-4: Workflows (все 6)
День 5-6: Intermediate (выборочно)
День 7: Advanced (01_embedding_systems)
```

**Результат**: Понимание внутренних механизмов, создание своих решений

### Путь 3: Эксперт (2 недели)

```
Неделя 1: Beginner + Intermediate (все)
Неделя 2: Advanced (все) + Workflows (все)
```

**Результат**: Production развертывание, оптимизация, расширение

---

## По темам

### Хочу понять математику

1. [Tool Selection](intermediate/02_tool_selection.md) - Softmax и температура
2. [Training System](intermediate/04_training_system.md) - Policy Gradient
3. [Graph Algorithms](intermediate/01_graph_algorithms.md) - Поиск путей

### Хочу настроить под свои задачи

1. [Custom Tools](intermediate/05_custom_tools.md) - Свои инструменты
2. [NLI Parsing](intermediate/03_nli_parsing.md) - Расширение NLI
3. [Extending System](advanced/03_extending_system.md) - Кастомизация

### Хочу оптимизировать

1. [Performance Tuning](advanced/02_performance_tuning.md) - Скорость

### Хочу создать инфраструктуру
1. [Embedding Systems](deployment/01_embedding_systems.md) - Качество
2. [Production Deployment](deployment/02_production_deployment.md) - Масштабирование

---

## Дополнительные ресурсы

### Примеры кода

- `examples/Python/` - Основные примеры
- `examples/Python/nli/` - Примеры NLI
- `src/GraphArchitectLib/Web/` - Web API примеры

### Документация

- `src/GraphArchitectLib/Web/README_FINAL.md` - Web API
- `src/GraphArchitectLib/grapharchitect/README.md` - Библиотека
- `src/GraphArchitectLib/Tests/README.md` - Тесты

### Тесты

- `src/GraphArchitectLib/Tests/` - 235 unit тестов
- `src/GraphArchitectLib/Web/test_*.py` - Integration тесты

---

## Помощь

### Если застряли

1. Проверьте Prerequisites туториала
2. Убедитесь что выполнили предыдущие шаги
3. Смотрите логи: `python main.py` покажет ошибки
4. Запустите диагностику: `python diagnose.py`

### Частые вопросы

**Q**: С чего начать?

**A**: [Quick Start](beginner/01_quick_start.md) - 5 минут

**Q**: Как создать свой инструмент?

**A**: [Custom Tools](intermediate/05_custom_tools.md)

**Q**: Почему низкая точность NLI?

**A**: Используйте Infinity embeddings - [Embedding Systems](deployment/01_embedding_systems.md)

**Q**: Как ускорить для большого датасета?

**A**: Используйте Faiss - [Embedding Systems](deployment/01_embedding_systems.md)

---

## Статус туториалов

- ✅ Beginner: 5/5 (100%)
- ✅ Intermediate: 5/5 (100%)
- ✅ Advanced: 5/5 (100%)
- ✅ Workflows: 6/6 (100%)

**Всего**: 21 туториал, ~575 минут обучающего материала

---

**Начните здесь**: [Быстрый старт](beginner/01_quick_start.md)
