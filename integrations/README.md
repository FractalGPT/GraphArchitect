# GraphArchitect Integrations

Интеграции GraphArchitect с популярными фреймворками и инструментами.

---

## Доступные интеграции

### LangChain

**Статус**: Полностью реализовано

**Что дает**:
- Использование GraphArchitect tools в LangChain agents
- Использование LangChain tools в GraphArchitect
- Гибридное выполнение с объединенными возможностями

**Документация**: [langchain/README.md](langchain/README.md)

**Примеры**: [langchain/examples/](langchain/examples/)

---

## Планируемые интеграции

### AutoGPT

Интеграция с AutoGPT для:
- Автономное выполнение задач
- GraphArchitect как execution layer
- Обучение на результатах

### LlamaIndex

Интеграция с LlamaIndex для:
- RAG (Retrieval-Augmented Generation)
- Работа с документами
- Векторные хранилища в GraphArchitect

### CrewAI

Интеграция с CrewAI для:
- Multi-agent сценарии
- Распределенное выполнение
- Координация агентов

---

## Быстрый старт

### LangChain интеграция

```bash
cd integrations/langchain

# Установка
pip install -r requirements.txt

# Примеры
cd examples
python example_01_basic_integration.py
```

---

## Архитектура

### Принципы интеграции

1. **Adapter Pattern**: Обертки для конвертации
2. **Composition**: Не наследование, а композиция
3. **Graceful Degradation**: Работа при недоступности компонентов
4. **No Vendor Lock-in**: Легко использовать оба фреймворка

### Уровни интеграции

```
Level 1: Basic Adapters
  - GraphArchitect Tool → LangChain Tool
  - LangChain Tool → GraphArchitect Tool

Level 2: Hybrid Execution
  - Объединенный граф инструментов
  - GraphArchitect планирование для всех

Level 3: Advanced Features
  - Shared learning
  - Unified monitoring
  - Cross-framework optimization
```

---

## Roadmap

### v1.0 (Текущая)

- Базовые адаптеры
- Гибридный executor
- Примеры

### v1.1 (Планируется)

- Async поддержка
- Streaming
- Callbacks интеграция

### v2.0 (Будущее)

- Автоматическое определение коннекторов
- Shared vector stores
- Unified memory

---

## Итоги

**Доступно**:
- LangChain интеграция (полная)

**В разработке**:
- AutoGPT интеграция
- LlamaIndex интеграция

**Статус**: Production-ready для LangChain

---

**Начните с**: [langchain/README.md](langchain/README.md)
