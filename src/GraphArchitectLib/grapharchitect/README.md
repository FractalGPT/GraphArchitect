# GraphArchitect

**GraphArchitect** - система планирования и выполнения задач с использованием графа инструментов. Переписанная версия FractalAgentsAI.GraphBasedAgents с C# на Python, где концепция "агентов" заменена на "инструменты".

## 📋 Описание системы

Система работает в 5 этапов - от описания задачи на естественном языке до формирования ответа и дообучения:

### 1. Естественно-языковой интерфейс (ЕЯИ / NLI)

Задача формируется текстом на русском языке и попадает в модуль ЕЯИ, где преобразовывается в вид:

```
{входной коннектор, выходной коннектор, текстовое описание задачи}
```

Нейронная сеть ЕЯИ формирует пару входной-выходной коннекторы, используя k-NN few-shot подход.

### 2. Граф инструментов

Граф, где:
- **Вершины** - строгие представления коннекторов (форматы данных)
- **Рёбра** - группы инструментов, преобразующих данные из формата A в формат B
- **Вес ребра** - обратная величина от среднего качества выполнения

Например:
- Все возможные LLM, которые могут ответить на вопрос
- Различные конвертеры из JPG в матрицу или тензор

### 3. Поиск стратегии

Для определения цепочки групп инструментов используются алгоритмы поиска кратчайшего пути:

- **A*** - поиск одного пути с эвристикой
- **Dijkstra** - поиск одного кратчайшего пути
- **Yen** - поиск топ-N путей
- **Ant Colony Optimization (ACO)** - муравьиный алгоритм для топ-N путей

### 4. Выполнение программы

Ключевой этап выбора инструментов:

1. Формируется векторное представление задачи (эмбеддинг)
2. Эмбеддинг отправляется всем инструментам в группе
3. Получаем **логиты** от всех инструментов (ненормированные оценки качества)
4. Отбираем **топ-K** инструментов с наибольшими логитами
5. Вычисляем **температуру группы**: 
   ```
   T = (C/K) * Σ√(D_k* / m_k)
   ```
   где:
   - C - константа
   - K - количество инструментов
   - D_k* - оценка дисперсии оценок инструмента k
   - m_k - объем выборки для обучения инструмента k
   
6. Применяем **softmax с температурой**:
   ```
   P(k) = exp(logit_k / T) / Σ exp(logit_i / T)
   ```
   
7. Выбираем инструмент через **сэмплирование** из распределения
8. Сохраняем градиентную информацию для обучения

Результат сохраняется в БД вместе с метриками (время, стоимость, качество).

### 5. Дообучение системы

На финальном этапе происходит:

- **Дообучение инструментов** (Policy Gradient):
  ```
  ∇ = (R - baseline) * ∇log P(a|s)
  ```
  
- **Обновление эмбеддингов** (Contrastive Learning):
  - Притягивание к успешным задачам
  - Отталкивание от неуспешных
  
- **Сохранение датасета** для дообучения эмбеддеров

## 🏗️ Архитектура

```
graphachitect/
├── entities/              # Модели данных
│   ├── base_tool.py      # Базовый класс инструмента (ранее BaseAgent)
│   ├── tool_metadata.py  # Метаданные: репутация, стоимость, статистика
│   ├── task_definition.py
│   └── connectors/       # Форматы данных (вершины графа)
│
├── algorithms/           # Алгоритмы поиска пути
│   ├── graph/           # Базовые структуры графа
│   └── pathfinding/     # Dijkstra, A*, Yen, ACO
│
└── services/            # Основная логика
    ├── nli/            # Естественно-языковой интерфейс
    ├── embedding/      # Векторизация текста
    ├── selection/      # Выбор инструментов (softmax + температура)
    ├── execution/      # Оркестрация выполнения
    ├── feedback/       # Обратная связь и критики
    └── training/       # Дообучение инструментов
```

## 🚀 Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd graphachitect

# Установить зависимости
pip install -r requirements.txt
```

### 🎯 Полноценный пример

Запустите готовый пример с интерактивным выбором алгоритмов:

```bash
cd examples
python pathfind_test.py
```

Или используйте скрипт запуска:

**Windows:**
```bash
cd examples
run_example.bat
```

**Linux/Mac:**
```bash
cd examples
chmod +x run_example.sh
./run_example.sh
```

Пример демонстрирует:
- ✅ Создание графа инструментов (6 тестовых инструментов)
- ✅ Выбор алгоритма поиска (Dijkstra, Yen, A*, Ant Colony)
- ✅ Поиск оптимальной стратегии
- ✅ Выполнение с softmax и температурой
- ✅ Автоматическую оценку качества
- ✅ Дообучение инструментов

См. подробности в [examples/README.md](examples/README.md)

### Базовый пример

```python
from graphachitect.entities import BaseTool, TaskDefinition
from graphachitect.entities.connectors import Connector
from graphachitect.services.embedding import SimpleEmbeddingService
from graphachitect.services.selection import InstrumentSelector
from graphachitect.services import GraphBuilder, GraphStrategyFinder
from graphachitect.services.execution import ExecutionOrchestrator

# 1. Создать инструменты
class TextToSummaryTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.input = Connector(data_format="text", semantic_format="question")
        self.output = Connector(data_format="text", semantic_format="summary")
        self.metadata.tool_name = "Summarizer"
        self.metadata.reputation = 0.8
    
    def execute(self, input_data):
        return f"Summary of: {input_data}"

# 2. Инициализировать сервисы
embedding_service = SimpleEmbeddingService()
selector = InstrumentSelector(temperature_constant=1.0)
strategy_finder = GraphStrategyFinder()
orchestrator = ExecutionOrchestrator(
    embedding_service,
    selector,
    strategy_finder
)

# 3. Создать задачу
task = TaskDefinition(
    description="Суммаризировать текст",
    input_connector=Connector(data_format="text", semantic_format="question"),
    output_connector=Connector(data_format="text", semantic_format="summary"),
    input_data="Длинный текст для суммаризации..."
)

# 4. Выполнить задачу
tools = [TextToSummaryTool()]
context = orchestrator.execute_task(task, tools, path_limit=1, top_k=5)

print(f"Результат: {context.result}")
print(f"Статус: {context.status}")
print(f"Время: {context.total_time:.2f}с")
```

## 🔑 Ключевые особенности

### 1. Softmax с температурой

Выбор инструмента происходит не детерминированно, а вероятностно:

- **Высокая температура** (T >> 1) → более равномерное распределение (исследование)
- **Низкая температура** (T → 0) → концентрация на лучших (эксплуатация)
- **Адаптивная температура** зависит от объема обучающей выборки инструмента

### 2. Policy Gradient для обучения

Инструменты обучаются на основе обратной связи:

```python
advantage = reward - baseline
new_reputation = reputation + learning_rate * advantage
```

### 3. Contrastive Learning для эмбеддингов

Эмбеддинги инструментов адаптируются:
- Притягиваются к успешно решённым задачам
- Отталкиваются от неуспешных

### 4. Множественные алгоритмы поиска

Гибкий выбор алгоритма в зависимости от задачи:
- **Dijkstra/A*** - когда нужен один лучший путь
- **Yen/ACO** - когда нужны альтернативные варианты

## 📊 Метрики и обучение

Система собирает метрики на каждом этапе:

- **Качество** (quality_score): оценка от пользователя или автокритика
- **Время выполнения** (execution_time)
- **Стоимость** (cost)
- **Репутация инструмента** (reputation)
- **Дисперсия оценок** (variance_estimate)

Эти метрики используются для:
1. Выбора инструментов (через логиты)
2. Вычисления температуры (через дисперсию и размер выборки)
3. Дообучения (через Policy Gradient)

## 🔄 Сравнение с C# версией

| Концепция C# | Концепция Python | Описание |
|--------------|------------------|----------|
| `BaseAgent` | `BaseTool` | Базовый класс для инструментов |
| `AgentMetadata` | `ToolMetadata` | Метаданные инструмента |
| `AgentEdge` | `ToolEdge` | Ребро графа с группой инструментов |
| `GraphBasedAgents` | `GraphArchitect` | Название системы |

Все остальные компоненты сохранили свою функциональность и логику работы.

## 📚 Документация

Более подробная документация в директории `services/nli/`:
- `README.md` - описание естественно-языкового интерфейса
- `QUICKSTART.md` - быстрый старт с NLI
- `SEMANTICS.md` - описание семантических типов

## 🤝 Вклад в проект

Проект открыт для улучшений! Основные направления:

1. **Интеграция с реальными эмбеддингами**
   - OpenAI Embeddings API
   - Sentence Transformers
   - Multilingual models

2. **Улучшение NLI**
   - Fine-tuning на специфичных доменах
   - Интеграция с LLM (GPT-4, Claude)
   - Активное обучение

3. **Векторные БД**
   - FAISS для быстрого поиска
   - ChromaDB для персистентности
   - Milvus для масштабирования

4. **Мониторинг и визуализация**
   - Dashboard для метрик
   - Визуализация графа
   - A/B тестирование стратегий

## 📝 Лицензия

[Укажите лицензию]

## 👥 Авторы

FractalAgentsAI Team

---

**Примечание**: Это альфа-версия. Сервис эмбеддингов (`SimpleEmbeddingService`) использует заглушку. Для продакшена необходимо интегрировать реальные модели векторизации.
