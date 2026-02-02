# Интеграция GraphArchitect + LangChain

Полная двусторонняя интеграция между GraphArchitect и LangChain.

---

## Что это дает?

### GraphArchitect → LangChain

Используйте GraphArchitect инструменты в LangChain:
- Инструменты с обучением (Policy Gradient)
- Адаптивный выбор через softmax
- Граф-планирование в LangChain agents

### LangChain → GraphArchitect

Используйте LangChain tools в GraphArchitect:
- Доступ к богатой экосистеме LangChain
- Интеграции с API (Search, Wikipedia, и т.д.)
- Chains как инструменты GraphArchitect

### Гибридный подход

Объединение сильных сторон:
- Планирование графа от GraphArchitect
- Экосистема tools от LangChain
- Обучение Policy Gradient
- ReAct reasoning от LangChain

---

## Установка

### Зависимости

```bash
pip install langchain openai
pip install faiss-cpu numpy  # Для GraphArchitect
```

### Структура

```
integrations/langchain/
├── grapharchitect_to_langchain.py  # GA → LC адаптер
├── langchain_to_grapharchitect.py  # LC → GA адаптер
├── hybrid_executor.py              # Гибридный исполнитель
├── examples/
│   ├── example_01_basic_integration.py
│   ├── example_02_langchain_agent.py
│   └── example_03_hybrid_execution.py
├── README.md
└── requirements.txt
```

---

## Быстрый старт

### Пример 1: GraphArchitect tools в LangChain

```python
from grapharchitect_to_langchain import convert_grapharchitect_tools_to_langchain
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

# GraphArchitect инструменты
ga_tools = [...]  # Ваши GraphArchitect BaseTool

# Конвертация
langchain_tools = convert_grapharchitect_tools_to_langchain(ga_tools)

# Создание LangChain агента
llm = OpenAI(temperature=0.7)
agent = initialize_agent(
    tools=langchain_tools,
    llm=llm,
    agent="zero-shot-react-description"
)

# Использование
result = agent.run("Classify this text")
```

### Пример 2: LangChain tools в GraphArchitect

```python
from langchain_to_grapharchitect import convert_langchain_tools_to_grapharchitect
from langchain.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from grapharchitect.entities.connectors.connector import Connector

# LangChain tools
lc_tools = [
    WikipediaQueryRun(),
    DuckDuckGoSearchRun()
]

# Конвертация с указанием коннекторов
ga_tools = convert_langchain_tools_to_grapharchitect(
    lc_tools,
    connector_mappings={
        "Wikipedia": (Connector("text", "query"), Connector("text", "findings")),
        "DuckDuckGo": (Connector("text", "query"), Connector("text", "findings"))
    }
)

# Использование в GraphArchitect
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator

orchestrator = ExecutionOrchestrator(...)
context = orchestrator.execute_task(task, ga_tools)
```

### Пример 3: Гибридное выполнение

```python
from hybrid_executor import HybridExecutor

# Создаем гибридный исполнитель
executor = HybridExecutor()

# Добавляем GraphArchitect tools
executor.add_grapharchitect_tools(grapharchitect_tools)

# Добавляем LangChain tools
executor.add_langchain_tools(langchain_tools, connector_mappings)

# Выполнение - GraphArchitect планирует, используя ОБА набора
context = executor.execute_task(
    description="Research and analyze",
    input_data="Topic to research"
)
```

---

## Компоненты интеграции

### 1. GraphArchitectToolWrapper

Обертка для использования GraphArchitect tools в LangChain.

**Возможности**:
- Автоматическая конвертация метаданных
- Сохранение информации о коннекторах
- Поддержка sync/async выполнения

**Использование**:
```python
from grapharchitect_to_langchain import GraphArchitectToolWrapper

wrapped = GraphArchitectToolWrapper(grapharchitect_tool)
result = wrapped.run("input data")  # LangChain style
```

### 2. LangChainToolWrapper

Обертка для использования LangChain tools в GraphArchitect.

**Возможности**:
- Указание коннекторов для графа
- Интеграция в систему обучения
- Метрики и репутация

**Использование**:
```python
from langchain_to_grapharchitect import LangChainToolWrapper

wrapped = LangChainToolWrapper(
    langchain_tool,
    input_connector=Connector("text", "query"),
    output_connector=Connector("text", "findings")
)

result = wrapped.execute("input")  # GraphArchitect style
```

### 3. HybridExecutor

Гибридный исполнитель задач.

**Возможности**:
- Объединение инструментов из обеих систем
- GraphArchitect планирование для всех
- Softmax выбор для всех
- Обучение через Policy Gradient

**Использование**:
```python
from hybrid_executor import HybridExecutor

executor = HybridExecutor()
executor.add_grapharchitect_tools(ga_tools)
executor.add_langchain_tools(lc_tools)

context = executor.execute_task(description, input_data)
```

---

## Архитектура интеграции

### Двусторонняя конвертация

```
GraphArchitect BaseTool <─────> LangChain Tool
         ↓                           ↓
    execute(data)               run(input)
         ↓                           ↓
  input|output               description only
    connectors
```

### Гибридное выполнение

```
Задача
  ↓
HybridExecutor
  ├─ GraphArchitect tools (нативные)
  ├─ LangChain tools (обернутые)
  └─ Все в одном графе
  ↓
GraphArchitect планирование
  - Поиск путей в графе
  - Softmax выбор
  - Вероятностное сэмплирование
  ↓
Выполнение (любой источник)
  ↓
Обучение (Policy Gradient)
```

---

## Примеры использования

### Пример: Исследование с Wikipedia

```python
from langchain.tools import WikipediaQueryRun
from langchain_to_grapharchitect import LangChainToolWrapper
from grapharchitect.entities.connectors.connector import Connector

# LangChain Wikipedia tool
wiki_tool = WikipediaQueryRun()

# Обертка для GraphArchitect
wiki_ga = LangChainToolWrapper(
    langchain_tool=wiki_tool,
    input_connector=Connector("text", "query"),
    output_connector=Connector("text", "findings")
)

# Теперь можно использовать в GraphArchitect workflow
# Wikipedia интегрирован в граф инструментов!
```

### Пример: GraphArchitect в LangChain Agent

```python
from grapharchitect_to_langchain import convert_grapharchitect_tools_to_langchain
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

# GraphArchitect инструменты с обучением
ga_tools = load_trained_tools()  # Уже обученные!

# Конвертация
lc_tools = convert_grapharchitect_tools_to_langchain(ga_tools)

# LangChain Agent использует обученные GraphArchitect tools
llm = OpenAI()
agent = initialize_agent(lc_tools, llm, agent="zero-shot-react-description")

# Планирование от LangChain, выполнение обученными инструментами
result = agent.run("Complex task requiring multiple steps")
```

---

## Преимущества интеграции

### Для пользователей GraphArchitect

- Доступ к LangChain ecosystem (100+ готовых tools)
- Интеграции: Wikipedia, Search, Calculator, Weather, и т.д.
- LangChain chains как building blocks
- Community tools

### Для пользователей LangChain

- Граф-планирование вместо sequential chains
- Softmax выбор вместо hardcoded logic
- Обучение инструментов через использование
- Адаптивная температура
- Метрики и репутация

### Гибридный подход

- Лучшее из обоих миров
- Гибкость в выборе инструментов
- Масштабируемость
- Production-ready

---

## Ограничения

### Текущие

1. **Коннекторы LangChain tools**:
   - LangChain не имеет концепции коннекторов
   - Нужно указывать вручную при конвертации

2. **Async выполнение**:
   - GraphArchitect в основном sync
   - LangChain имеет async поддержку
   - Текущая обертка fallback на sync

3. **Метаданные**:
   - LangChain tools не имеют репутации
   - Начальная репутация = 0.75

### Обходные пути

1. **Connector mappings**: Указывайте при конвертации
2. **Async**: Используется sync fallback
3. **Reputation**: Обучается автоматически после использования

---

## Конфигурация

### requirements.txt

```
langchain>=0.1.0
openai>=1.0.0
grapharchitect  # Локальный пакет
```

### Опциональные зависимости

```
# Для дополнительных LangChain tools
wikipedia>=1.4.0
duckduckgo-search>=4.0.0
google-search-results>=2.4.0

# Для векторных хранилищ
chromadb>=0.4.0
faiss-cpu>=1.7.4
```

---

## Запуск примеров

```bash
cd integrations/langchain/examples

# Базовая интеграция
python example_01_basic_integration.py

# LangChain Agent
python example_02_langchain_agent.py

# Гибридное выполнение
python example_03_hybrid_execution.py
```

---

## Расширенные сценарии

### 1. RAG (Retrieval-Augmented Generation)

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# LangChain RAG chain
vectorstore = Chroma(embedding_function=OpenAIEmbeddings())
qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever())

# Обертка для GraphArchitect
from langchain_to_grapharchitect import LangChainChainWrapper

rag_tool = LangChainChainWrapper(
    chain=qa_chain,
    name="RAG QA",
    description="Question answering with retrieval",
    input_connector=Connector("text", "question"),
    output_connector=Connector("text", "answer")
)

# Теперь RAG chain - инструмент в GraphArchitect графе!
```

### 2. Специализированные Chains

```python
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate

# LangChain chain для specific задачи
prompt = PromptTemplate(template="Summarize: {text}", input_variables=["text"])
chain = LLMChain(llm=llm, prompt=prompt)

# В GraphArchitect
summarizer_tool = LangChainChainWrapper(
    chain=chain,
    name="LLM Summarizer",
    input_connector=Connector("text", "document"),
    output_connector=Connector("text", "summary"),
    input_key="text"
)
```

---

## Тестирование

```bash
# Проверка зависимостей
python -c "import langchain; import grapharchitect; print('OK')"

# Запуск примеров
cd examples
python example_01_basic_integration.py
```

---

## Архитектурные решения

### Почему обертки, а не наследование?

**Composition over inheritance**:
- Гибкость
- Избежание конфликтов методов
- Четкое разделение ответственностей

### Почему HybridExecutor?

**Single point of integration**:
- Единый интерфейс
- Управление всеми инструментами
- Переиспользование GraphArchitect логики

---

## Production использование

### Рекомендации

1. **Кеширование**: Используйте LangChain caching для LLM вызовов
2. **Мониторинг**: Логируйте использование обоих типов tools
3. **Обучение**: Сохраняйте метрики GraphArchitect tools
4. **Fallback**: Graceful degradation при ошибках

### Пример production конфигурации

```python
from hybrid_executor import HybridExecutor
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

# Кеширование LangChain
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# Гибридный исполнитель с настройками
executor = HybridExecutor(
    temperature_constant=0.5,  # Меньше исследования в production
    learning_rate=0.01
)

# Добавление инструментов
executor.add_grapharchitect_tools(ga_tools)
executor.add_langchain_tools(lc_tools, connector_mappings)
```

---

## Roadmap

### Планируется

- [ ] Async поддержка для GraphArchitect
- [ ] Streaming responses
- [ ] Callbacks integration
- [ ] Memory интеграция
- [ ] Векторные хранилища в GraphArchitect граф

---

## Итоги

**Создано**:
- 3 файла адаптеров
- 3 примера использования
- Полная документация

**Возможности**:
- Двусторонняя интеграция
- Гибридное выполнение
- Production-ready

**Использование**:
- Готово к использованию
- Примеры работают
- Документировано

---

**Начните с**: `examples/example_01_basic_integration.py`
