# 💾 SQLite интеграция - Руководство

## 🎯 Что это?

Полная замена **InMemoryRepository** на **SQLite3** для персистентного хранения:
- ✅ Агенты (вместо хардкода)
- ✅ Workflows
- ✅ Чаты и документы
- ✅ История выполнений
- ✅ Обратная связь для обучения
- ✅ Метрики инструментов

**SQLite3 включен в Python** - никаких дополнительных зависимостей!

---

## 🚀 Быстрый старт

### Шаг 1: Инициализация БД

```bash
cd Web
python db_manager.py init
```

**Результат:** Создан файл `grapharchitect.db` с таблицами

### Шаг 2: Загрузка агентов

```bash
python db_manager.py load_agents
```

**Результат:** 24 агента из `agent_library.py` загружены в БД

### Шаг 3: Проверка

```bash
python db_manager.py list_agents
```

**Результат:** Список всех агентов в БД

### Шаг 4: Запуск сервера

```bash
python main.py
```

**Результат:** Сервер использует SQLite автоматически!

---

## 📁 Структура БД

### Таблицы

| Таблица | Назначение | Записей (начально) |
|---------|------------|-------------------|
| `agents` | Библиотека агентов | 24 |
| `workflows` | Цепочки выполнения | 0 |
| `chats` | Информация о чатах | 0 |
| `documents` | Загруженные файлы | 0 |
| `executions` | История выполнений | 0 |
| `feedbacks` | Обратная связь | 0 |
| `tool_metrics` | Метрики после обучения | 0 |

### Схема БД

```sql
-- Агенты (вместо хардкода!)
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    icon TEXT,
    color TEXT,
    specialization TEXT,
    capabilities TEXT,  -- JSON
    cost REAL,
    metrics TEXT,       -- JSON
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Workflows
CREATE TABLE workflows (
    chat_id TEXT PRIMARY KEY,
    name TEXT,
    steps TEXT,         -- JSON
    agents TEXT,        -- JSON
    files TEXT,         -- JSON
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- История выполнений (для обучения!)
CREATE TABLE executions (
    execution_id TEXT PRIMARY KEY,
    task_id TEXT,
    chat_id TEXT,
    task_description TEXT,
    status TEXT,        -- COMPLETED/FAILED
    selected_tools TEXT,    -- JSON
    gradient_traces TEXT,   -- JSON
    result TEXT,
    total_time REAL,
    total_cost REAL,
    created_at TIMESTAMP
);

-- Обратная связь
CREATE TABLE feedbacks (
    feedback_id INTEGER PRIMARY KEY,
    task_id TEXT,
    source TEXT,        -- USER/AUTO_CRITIC
    quality_score REAL,
    success INTEGER,
    comment TEXT,
    created_at TIMESTAMP
);

-- Метрики инструментов (после обучения)
CREATE TABLE tool_metrics (
    agent_id TEXT PRIMARY KEY,
    reputation REAL,    -- Обновляется!
    mean_cost REAL,
    training_sample_size INTEGER,
    variance_estimate REAL,
    quality_scores TEXT,    -- JSON
    last_training_date TIMESTAMP
);
```

---

## 🔧 Команды управления БД

### Инициализация

```bash
# Создать таблицы
python db_manager.py init

# С другим файлом БД
python db_manager.py --db-path mydb.db init
```

### Управление агентами

```bash
# Загрузить агентов из agent_library.py
python db_manager.py load_agents

# Перезаписать существующих
python db_manager.py load_agents --force

# Показать всех агентов
python db_manager.py list_agents

# Добавить нового агента (интерактивно)
python db_manager.py add_agent

# Экспорт в JSON
python db_manager.py export --output agents.json

# Импорт из JSON
python db_manager.py import_agents --input agents.json
```

### Статистика

```bash
# Показать статистику БД
python db_manager.py stats
```

**Вывод:**
```
Размер таблиц:
  agents                24 записей
  executions            15 записей
  feedbacks             15 записей
  tool_metrics          8 записей

Выполнения:
  Завершено:  13 (86.7%)
  Провалено:  2 (13.3%)

Качество:
  Средняя оценка: 0.863
```

### Backup и очистка

```bash
# Создать backup
python db_manager.py backup
# → grapharchitect_backup_20260127_143022.db

# Очистить все данные
python db_manager.py clear

# Без подтверждения
python db_manager.py clear --force
```

---

## 🔄 Как работает интеграция

### 1. При запуске сервера

```python
# repository.py
def get_repository(use_sqlite=True):
    if use_sqlite:
        # ✅ Используется SQLite (АВТОМАТИЧЕСКИ!)
        from sqlite_repository import get_sqlite_repository
        return get_sqlite_repository()
    else:
        # Fallback на InMemory
        return InMemoryRepository()
```

### 2. Загрузка агентов

```python
# agent_library.py
def get_all_agents(use_db=True):
    if use_db:
        # ✅ Загружаем из БД
        repo = get_sqlite_repository()
        return repo.get_all_agents()
    else:
        # Fallback на хардкод
        return list(AGENT_LIBRARY.values())
```

### 3. Конверсия в BaseTool

```python
# grapharchitect_bridge.py
def _convert_agents_to_tools(self):
    agents = get_all_agents()  # ← Из БД!
    
    tools = []
    for agent in agents:
        tool = AgentTool(agent)  # ← Agent из БД → BaseTool
        tools.append(tool)
    
    return tools
```

### 4. После выполнения - сохранение

```python
# grapharchitect_bridge.py
async def _auto_evaluate_and_train(context):
    # 1. Обучение инструментов
    training.train_all_tools(tools)
    
    # 2. Сохранение метрик в БД
    for tool in tools:
        repo.save_tool_metrics(
            agent_id=tool.agent_id,
            reputation=tool.metadata.reputation,  # ← Обновленная!
            training_sample_size=tool.metadata.training_sample_size,
            ...
        )
    
    # 3. Сохранение истории
    repo.save_execution(
        task_id=context.task_id,
        selected_tools=[...],
        gradient_traces=[...],
        result=context.result
    )
    
    # 4. Сохранение feedback
    repo.save_feedback(
        task_id=context.task_id,
        quality_score=0.87,
        source="AUTO_CRITIC"
    )
```

---

## 📊 Схема данных

### До (InMemory)

```
Запуск сервера
    ↓
Данные в памяти:
  • agents: [] (пусто)
  • workflows: {}
  • chats: {}
    ↓
При каждом запросе:
  • Загружаются из agent_library.py
    ↓
Перезапуск сервера
    ↓
ВСЕ ДАННЫЕ ПОТЕРЯНЫ ❌
```

### После (SQLite)

```
Запуск сервера
    ↓
Подключение к БД:
  grapharchitect.db
    ↓
Загрузка из БД:
  • SELECT * FROM agents → 24 агента
  • SELECT * FROM workflows → история
  • SELECT * FROM tool_metrics → метрики обучения
    ↓
Использование в GraphArchitect
    ↓
После выполнения:
  • INSERT INTO executions (...)
  • INSERT INTO feedbacks (...)
  • UPDATE tool_metrics (reputation ↑)
    ↓
Перезапуск сервера
    ↓
ВСЕ ДАННЫЕ СОХРАНЕНЫ ✅
```

---

## 🎓 Обучение с SQLite

### Сценарий: Улучшение репутации

```sql
-- НАЧАЛЬНОЕ СОСТОЯНИЕ (из agent_library.py)
INSERT INTO agents (id, name, metrics)
VALUES ('agent-gpt4', 'GPT-4', '{"avgScore": 0.98}');

INSERT INTO tool_metrics (agent_id, reputation)
VALUES ('agent-gpt4', 0.98);

-- ВЫПОЛНЕНИЕ #1
-- Качество: 0.95
UPDATE tool_metrics 
SET reputation = 0.98 + 0.01 * (0.95 - 0.98) = 0.9797,
    training_sample_size = 11
WHERE agent_id = 'agent-gpt4';

-- ВЫПОЛНЕНИЕ #2
-- Качество: 0.96
UPDATE tool_metrics 
SET reputation = 0.9797 + 0.01 * (0.96 - 0.9797) = 0.9797,
    training_sample_size = 12
WHERE agent_id = 'agent-gpt4';

-- ... после 100 выполнений ...

SELECT reputation, training_sample_size 
FROM tool_metrics 
WHERE agent_id = 'agent-gpt4';
-- reputation: 0.96 (улучшилась на основе реальных данных!)
-- training_sample_size: 110
```

---

## 🔍 SQL запросы для анализа

### Статистика обучения

```sql
-- Топ-5 инструментов по репутации
SELECT agent_id, tool_name, reputation, training_sample_size
FROM tool_metrics
ORDER BY reputation DESC
LIMIT 5;

-- Средняя оценка качества
SELECT AVG(quality_score) as avg_quality
FROM feedbacks;

-- Успешность по типам агентов
SELECT a.type, 
       COUNT(*) as executions,
       AVG(f.quality_score) as avg_quality
FROM executions e
JOIN agents a ON e.selected_tools LIKE '%' || a.name || '%'
LEFT JOIN feedbacks f ON e.task_id = f.task_id
GROUP BY a.type
ORDER BY avg_quality DESC;
```

### История выполнений

```sql
-- Последние 10 выполнений
SELECT task_description, status, total_time, total_cost, created_at
FROM executions
ORDER BY created_at DESC
LIMIT 10;

-- Самые дорогие выполнения
SELECT task_description, total_cost, selected_tools
FROM executions
ORDER BY total_cost DESC
LIMIT 5;
```

### Обратная связь

```sql
-- Распределение оценок
SELECT 
    CASE 
        WHEN quality_score >= 0.9 THEN 'Отлично'
        WHEN quality_score >= 0.7 THEN 'Хорошо'
        WHEN quality_score >= 0.5 THEN 'Средне'
        ELSE 'Плохо'
    END as rating,
    COUNT(*) as count
FROM feedbacks
GROUP BY rating
ORDER BY MIN(quality_score) DESC;
```

---

## 🔌 API примеры с БД

### Получение метрик из БД

```bash
# Метрики конкретного агента
curl http://localhost:8000/api/training/tools/agent-gpt4

# Ответ (данные из БД!):
{
  "agent_id": "agent-gpt4",
  "tool_name": "GPT-4 Classifier",
  "reputation": 0.967,        ← Обновлено обучением!
  "training_sample_size": 127,  ← Реальное количество
  "variance_estimate": 0.045,
  "quality_scores_count": 127
}
```

### Статистика обучения

```bash
curl http://localhost:8000/api/training/statistics

# Ответ (из БД!):
{
  "total_executions": 127,
  "average_quality": 0.863,
  "success_rate": 0.874
}
```

---

## 🛠️ Управление агентами

### Добавить нового агента

```bash
python db_manager.py add_agent
```

**Интерактивный ввод:**
```
ID агента: agent-custom-analyzer
Название: Custom Analyzer
Тип: analysis
Иконка: 🔬
Цвет: #10b981
Специализация: Кастомный анализ данных
Стоимость: 0.02

✅ Агент добавлен!
```

Агент **сразу доступен** в GraphArchitect!

### Экспорт/Импорт агентов

```bash
# Экспорт в JSON
python db_manager.py export --output my_agents.json

# Редактирование в редакторе
# ...

# Импорт обратно
python db_manager.py import_agents --input my_agents.json
```

---

## 📈 Мониторинг обучения

### Запрос 1: Как изменилась репутация

```sql
-- Исходная репутация (из agents)
SELECT id, name, json_extract(metrics, '$.avgScore') as initial_reputation
FROM agents
WHERE id = 'agent-gpt4';
-- → 0.98

-- Текущая репутация (после обучения)
SELECT agent_id, reputation, training_sample_size
FROM tool_metrics
WHERE agent_id = 'agent-gpt4';
-- → 0.967, 127 (немного упала, но на основе реальных данных!)
```

### Запрос 2: Прогресс обучения

```sql
-- История оценок качества
SELECT 
    e.created_at,
    e.task_description,
    f.quality_score
FROM executions e
JOIN feedbacks f ON e.task_id = f.task_id
WHERE e.selected_tools LIKE '%GPT-4%'
ORDER BY e.created_at;
```

### Запрос 3: Сравнение инструментов

```sql
SELECT 
    tm.agent_id,
    tm.tool_name,
    tm.reputation,
    tm.training_sample_size,
    a.cost
FROM tool_metrics tm
JOIN agents a ON tm.agent_id = a.id
ORDER BY tm.reputation DESC;
```

---

## 🔄 Миграция данных

### Из InMemory → SQLite

```python
# Если у вас были данные в InMemory или FileRepository

from repository import InMemoryRepository
from sqlite_repository import get_sqlite_repository

# Загружаем старые данные
old_repo = InMemoryRepository()
# ... загрузка из файлов ...

# Переносим в SQLite
new_repo = get_sqlite_repository()

for chat_id, workflow in old_repo._workflows.items():
    new_repo.save_workflow(workflow)

print("✅ Данные перенесены в SQLite")
```

### Backup существующих данных

```bash
# Создать backup перед миграцией
python db_manager.py backup

# Результат: grapharchitect_backup_20260127_143022.db
```

---

## 🧪 Тестирование с SQLite

### Тест 1: Проверка сохранения

```python
from sqlite_repository import get_sqlite_repository

repo = get_sqlite_repository()

# Сохраняем агента
agent = Agent(id="test", name="Test Agent", type="test", ...)
repo.save_agent(agent)

# Загружаем обратно
loaded = repo.get_agent("test")

assert loaded.id == "test"
assert loaded.name == "Test Agent"
```

### Тест 2: Проверка обучения

```python
# Выполняем задачу
context = bridge.execute_task_full(...)

# Проверяем что данные сохранились
executions = repo.get_executions(limit=1)

assert len(executions) > 0
assert executions[0]['status'] == 'COMPLETED'

# Проверяем метрики
metrics = repo.get_tool_metrics('agent-gpt4')

assert metrics is not None
assert metrics['training_sample_size'] > 10
```

---

## 📊 Преимущества SQLite

### Vs InMemory

| Аспект | InMemory | SQLite |
|--------|----------|--------|
| Персистентность | ❌ Нет | ✅ Да |
| Скорость | ⚡ Быстро | ⚡ Быстро |
| Запросы | ❌ Нет | ✅ SQL |
| Backup | ❌ Нет | ✅ Копия файла |
| Объем данных | ⚠️ Ограничен RAM | ✅ Гибайты |

### Vs PostgreSQL

| Аспект | SQLite | PostgreSQL |
|--------|--------|------------|
| Установка | ✅ Встроен | ❌ Нужен сервер |
| Конфигурация | ✅ Простая | ❌ Сложная |
| Многопользовательность | ⚠️ Ограничена | ✅ Полная |
| Масштабируемость | ⚠️ До ~1GB | ✅ Терабайты |
| Для разработки | ✅ Идеально | ⚠️ Избыточно |
| Для продакшена | ⚠️ До 10K req/day | ✅ Миллионы |

**Вывод:** SQLite идеален для старта и разработки!

---

## 🔧 Конфигурация

### Изменение пути к БД

**В repository.py:**
```python
def get_repository(use_sqlite=True):
    if use_sqlite:
        # Укажите свой путь
        return get_sqlite_repository(db_path="data/my_database.db")
```

**Или через переменную окружения:**
```python
import os

db_path = os.getenv("GRAPHARCHITECT_DB_PATH", "grapharchitect.db")
repo = get_sqlite_repository(db_path)
```

### Создать .env файл

```bash
# .env
GRAPHARCHITECT_DB_PATH=./data/grapharchitect.db
USE_SQLITE=true
```

---

## 🐛 Troubleshooting

### Ошибка: "database is locked"

**Причина:** Другой процесс использует БД

**Решение:**
```python
# В database.py
conn = sqlite3.connect(self.db_path, timeout=10.0)
```

### Ошибка: "no such table: agents"

**Причина:** Таблицы не созданы

**Решение:**
```bash
python db_manager.py init
```

### Агенты не загружаются из БД

**Проверка:**
```bash
python db_manager.py stats
# Смотрите: agents     0 записей

# Если 0:
python db_manager.py load_agents
```

---

## 📦 Что изменилось в коде

### Новые файлы (3):

1. `database.py` - Класс Database для работы с SQLite
2. `sqlite_repository.py` - SQLiteRepository (замена InMemory)
3. `db_manager.py` - CLI утилита управления

### Обновленные файлы (3):

1. `repository.py` - Добавлен выбор SQLite
2. `agent_library.py` - Загрузка агентов из БД
3. `grapharchitect_bridge.py` - Сохранение метрик в БД

---

## 🚀 Готово к использованию!

### Запуск с SQLite:

```bash
# 1. Инициализация
python db_manager.py init
python db_manager.py load_agents

# 2. Запуск сервера
python main.py

# Сервер автоматически использует SQLite!
```

### Проверка:

```bash
# Логи при запуске должны показать:
# ✅ SQLiteRepository инициализирован
# ✅ Используется SQLite репозиторий
# 📦 Загружено агентов из БД: 24
```

---

## 💡 Что дальше?

### Для разработки (готово):
- ✅ SQLite БД
- ✅ Агенты из БД
- ✅ История выполнений
- ✅ Метрики обучения

### Для продакшена (опционально):
- Миграция на PostgreSQL (больше данных)
- Добавление ChromaDB (векторный поиск)
- Репликация БД
- Мониторинг производительности

---

## 🎉 SQLite интеграция готова!

Теперь GraphArchitect Web API использует **настоящую БД** вместо памяти!

**Все данные сохраняются:**
- ✅ Агенты
- ✅ История выполнений
- ✅ Метрики обучения
- ✅ Обратная связь

**Запускайте и тестируйте!** 💾
