# GraphArchitect - Быстрый справочник

Краткий справочник по основным командам и концепциям.

---

## Быстрый старт

```bash
cd src/GraphArchitectLib/Web
python db_manager.py init
python db_manager.py load_agents
python main.py
```

Открыть: `http://localhost:8000`

---

## Основные команды

### База данных

```bash
python db_manager.py init           # Создать БД
python db_manager.py load_agents    # Загрузить инструменты
python db_manager.py list_agents    # Показать инструменты
python db_manager.py stats          # Статистика БД
python db_manager.py backup         # Создать backup
python db_manager.py clear --force  # Очистить данные
```

### Сервер

```bash
python main.py                      # Запустить сервер
python diagnose.py                  # Диагностика
python check_integration.py         # Проверка интеграции
python test_infinity_faiss.py       # Проверка Infinity+Faiss
```

### Примеры

```bash
cd examples/Python/nli
python example_01_basic_nli.py      # Базовый NLI
python example_02_nli_with_strategy.py  # NLI + стратегии
python example_03_nli_execution.py  # Полный цикл
```

---

## API Endpoints

### Chat & Workflow

```bash
# Создать workflow
POST /api/chat/{chat_id}/workflow

# Отправить сообщение (streaming)
POST /api/chat/{chat_id}/message/stream

# Получить workflow
GET /api/chat/{chat_id}/workflow
```

### Utility

```bash
# Health check
GET /api/health

# Список инструментов
GET /api/agents-library
```

---

## Ключевые концепции

### Граф инструментов

```
Вершины = Коннекторы (data|semantic)
Ребра = Инструменты
Вес = -log(reputation)
```

### Workflow

```
Task → NLI → Strategy → Selection → Execution → Training
```

### Выбор инструмента

```
Логит = cos_sim + log(rep)
T = (C/K) * Σ√(D/m)
P = softmax(логиты, T)
Выбор = sample(P)
```

### Обучение

```
advantage = reward - baseline
Δrep = lr * advantage
new_rep = clip(old_rep + Δrep, 0.01, 0.99)
```

---

## Алгоритмы планирования

```bash
dijkstra    # Один лучший путь (быстро)
astar       # С эвристикой
yen_3       # Топ-3 пути
yen_5       # Топ-5 (рекомендуется)
yen_10      # Топ-10
ant_3       # Муравьиный, топ-3
ant_5       # Муравьиный, топ-5
ant_10      # Муравьиный, топ-10
```

---

## Конфигурация

### В .env

```bash
# База данных
DATABASE_PATH=./grapharchitect.db

# Эмбеддинги
EMBEDDING_TYPE=simple  # или infinity
INFINITY_BASE_URL=http://localhost:7997

# k-NN
KNN_TYPE=naive  # или faiss
FAISS_INDEX_TYPE=FlatIP

# GraphArchitect
TEMPERATURE_CONSTANT=1.0
LEARNING_RATE=0.01

# Логирование
LOG_LEVEL=INFO
```

---

## Типовые workflow

### Customer Support

```
Classify → Respond → QA
```

### Content Creation

```
Research → Outline → Write → Style → QA
```

### Data Analysis

```
Parse → Analyze → Insights → Report
```

### Code Review

```
Parse → Style → Bugs → Security → Suggestions
```

---

## Troubleshooting

### Сервер не запускается

```bash
python diagnose.py
```

### БД не создана

```bash
python db_manager.py init
python db_manager.py load_agents
```

### Infinity недоступен

```bash
# Проверка
curl http://localhost:7997/health

# Запуск
docker run -d -p 7997:7997 michaelf34/infinity:latest
```

### Faiss не установлен

```bash
pip install faiss-cpu numpy
```

---

## Быстрые ссылки

### Документация

- [README](README.md) - Обзор туториалов
- [INDEX](INDEX.md) - Полный индекс
- [TUTORIAL_GUIDE](TUTORIAL_GUIDE.md) - Руководство

### Начало работы

- [Quick Start](beginner/01_quick_start.md) - 5 минут
- [Basic Concepts](beginner/02_basic_concepts.md) - 15 минут

### Готовые решения

- [Customer Support](workflows/customer_support.md)
- [Content Creation](workflows/content_creation.md)
- [Data Analysis](workflows/data_analysis.md)

### Продвинутое

- [Embedding Systems](deployment/01_embedding_systems.md)
- [Production Deployment](deployment/02_production_deployment.md)

---

**Начните здесь**: [README.md](README.md)
