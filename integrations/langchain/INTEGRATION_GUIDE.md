# Руководство по интеграции GraphArchitect + LangChain

Подробное руководство по использованию интеграции.

---

## Установка

### Шаг 1: Установить зависимости

```bash
cd integrations/langchain
pip install -r requirements.txt
```

### Шаг 2: Настроить API ключи

```bash
# Windows
set OPENAI_API_KEY=your-openai-key

# Linux/Mac
export OPENAI_API_KEY=your-openai-key
```

### Шаг 3: Проверить установку

```python
python -c "import langchain; import grapharchitect; print('OK')"
```

---

## Сценарии использования

### Сценарий 1: Добавить LangChain tools в GraphArchitect

**Задача**: Использовать Wikipedia и DuckDuckGo в GraphArchitect workflow

**Решение**:

```python
from langchain.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_to_grapharchitect import convert_langchain_tools_to_grapharchitect
from grapharchitect.entities.connectors.connector import Connector

# LangChain tools
wiki = WikipediaQueryRun()
search = DuckDuckGoSearchRun()

# Конвертация с указанием коннекторов
ga_tools = convert_langchain_tools_to_grapharchitect(
    [wiki, search],
    connector_mappings={
        "Wikipedia": (
            Connector("text", "query"),
            Connector("text", "findings")
        ),
        "duckduckgo_search": (
            Connector("text", "query"),
            Connector("text", "findings")
        )
    }
)

# Теперь используем в GraphArchitect
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator

orchestrator = ExecutionOrchestrator(...)
context = orchestrator.execute_task(task, ga_tools)
```

**Результат**: Wikipedia и Search интегрированы в граф, выбираются через softmax

---

### Сценарий 2: Использовать GraphArchitect в LangChain Agent

**Задача**: LangChain Agent с обученными GraphArchitect инструментами

**Решение**:

```python
from grapharchitect_to_langchain import create_langchain_agent_with_grapharchitect_tools
from langchain.llms import OpenAI

# Загрузить обученные GraphArchitect tools
# (они уже имеют репутацию и метрики)
from grapharchitect_bridge import get_bridge

bridge = get_bridge()
ga_tools = bridge.tools  # Обученные инструменты!

# Создать LangChain агента
llm = OpenAI(temperature=0.7)
agent = create_langchain_agent_with_grapharchitect_tools(
    grapharchitect_tools=ga_tools,
    llm=llm
)

# Выполнение
result = agent.run("Классифицировать и проанализировать запрос клиента")
```

**Результат**: LangChain Agent использует обученные инструменты с репутацией

---

### Сценарий 3: Гибридный workflow

**Задача**: Комбинировать GraphArchitect и LangChain инструменты

**Решение**:

```python
from hybrid_executor import HybridExecutor
from langchain.tools import WikipediaQueryRun

# Создаем executor
executor = HybridExecutor()

# Добавляем GraphArchitect tools (свои)
executor.add_grapharchitect_tools([
    MyClassifier(),
    MyAnalyzer(),
    MyReporter()
])

# Добавляем LangChain tools (community)
executor.add_langchain_tools([
    WikipediaQueryRun(),
    DuckDuckGoSearchRun()
])

# Выполнение - GraphArchitect планирует оптимальный путь
# используя ВСЕ доступные инструменты
context = executor.execute_task(
    description="Исследовать тему и создать отчет",
    input_data="Искусственный интеллект в медицине"
)
```

**Результат**: GraphArchitect находит оптимальный путь используя оба источника

---

## Продвинутые паттерны

### Паттерн 1: RAG с GraphArchitect планированием

```python
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_to_grapharchitect import LangChainChainWrapper

# LangChain RAG
vectorstore = Chroma(...)
qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever())

# Обертка для GraphArchitect
rag_tool = LangChainChainWrapper(
    chain=qa_chain,
    name="RAG QA",
    description="QA with document retrieval",
    input_connector=Connector("text", "question"),
    output_connector=Connector("text", "answer")
)

# Добавляем в граф
tools = [rag_tool, other_tools...]

# GraphArchitect решает когда использовать RAG
orchestrator.execute_task(task, tools)
```

### Паттерн 2: Multi-step reasoning

```python
# LangChain для reasoning, GraphArchitect для execution

from langchain.agents import AgentExecutor

# 1. LangChain Agent планирует шаги (ReAct)
agent = AgentExecutor(...)

# 2. Каждый шаг выполняется через GraphArchitect
#    (softmax выбор лучшего инструмента)

# Гибридный подход:
#   - Planning: LangChain (flexible reasoning)
#   - Execution: GraphArchitect (optimal selection)
```

### Паттерн 3: Ensemble методы

```python
# Несколько LangChain chains для одной задачи
chains = [
    create_qa_chain(llm1),
    create_qa_chain(llm2),
    create_qa_chain(llm3)
]

# Оборачиваем все как GraphArchitect tools
tools = [
    LangChainChainWrapper(chain, f"QA_{i}")
    for i, chain in enumerate(chains)
]

# GraphArchitect выбирает лучший через softmax
# Обучается на результатах
```

---

## Тестирование

### Unit тесты

```python
# test_integration.py
def test_grapharchitect_to_langchain():
    ga_tool = SimpleClassifier()
    lc_tool = GraphArchitectToolWrapper(ga_tool)
    
    result = lc_tool.run("test input")
    assert result is not None

def test_langchain_to_grapharchitect():
    lc_tool = Tool(name="Test", func=lambda x: x)
    ga_tool = LangChainToolWrapper(lc_tool)
    
    result = ga_tool.execute("test input")
    assert result is not None
```

### Integration тесты

```bash
cd examples
python example_01_basic_integration.py
python example_02_langchain_agent.py
python example_03_hybrid_execution.py
```

---

## Troubleshooting

### Ошибка: "LangChain not installed"

```bash
pip install langchain openai
```

### Ошибка: "GraphArchitect not available"

```bash
set PYTHONPATH=../../src/GraphArchitectLib;%PYTHONPATH%
```

### Ошибка: "No connector mapping"

Указывайте коннекторы при конвертации LangChain tools:

```python
converter_langchain_tools_to_grapharchitect(
    tools,
    connector_mappings={"ToolName": (input_conn, output_conn)}
)
```

---

## Best Practices

### 1. Указывайте коннекторы

LangChain tools не имеют коннекторов, указывайте их явно:

```python
connector_mappings={
    "Wikipedia": (Connector("text", "query"), Connector("text", "findings")),
    "Calculator": (Connector("text", "expression"), Connector("text", "result"))
}
```

### 2. Используйте HybridExecutor

Вместо ручной конвертации используйте HybridExecutor:

```python
executor = HybridExecutor()
executor.add_grapharchitect_tools(ga_tools)
executor.add_langchain_tools(lc_tools, mappings)
```

### 3. Мониторьте performance

```python
context = executor.execute_task(...)

print(f"Steps: {context.get_total_steps()}")
print(f"Time: {context.total_time}s")
print(f"Cost: ${context.total_cost}")
```

---

## Итоги

**Интеграция с LangChain**:
- Полностью реализована
- Протестирована
- Документирована
- Готова к использованию

**Файлы**:
- 3 адаптера
- 3 примера
- 4 документа
- requirements.txt

**Возможности**:
- Двусторонняя интеграция
- Гибридное выполнение
- Production-ready

---

**Начните с**: [langchain/README.md](langchain/README.md)
