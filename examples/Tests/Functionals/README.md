# Функциональные тесты GraphArchitect

Набор end-to-end и интеграционных тестов для проверки работы системы как целого.

---

## Типы тестов

### 1. End-to-End тесты (test_e2e_workflow.py)

**Проверяет**: Полный цикл выполнения задачи

**Сценарии**:
- Простой workflow (1 шаг)
- Многошаговый workflow (2+ шагов)
- Обучение и обновление репутации
- Снижение температуры с опытом
- Обработка отсутствия путей

**Запуск**:
```bash
pytest test_e2e_workflow.py -v
```

---

### 2. Web API тесты (test_web_api.py)

**Проверяет**: Работу Web API endpoints

**Сценарии**:
- Health check
- Получение списка инструментов
- Создание чата
- Streaming ответов
- Загрузка документов
- Получение списка документов
- Статистика обучения
- Создание workflow

**Требует**: Запущенный сервер (`python main.py`)

**Запуск**:
```bash
# Запустите сервер в другом терминале
cd src/GraphArchitectLib/Web
python main.py

# Запустите тесты
pytest test_web_api.py -v
```

---

### 3. Интеграционные сценарии (test_integration_scenarios.py)

**Проверяет**: Полные пользовательские сценарии

**Сценарии**:
- Customer Support (Classify → Respond → QA)
- Content Creation (Research → Outline → Write → Edit)
- Альтернативные пути (Yen algorithm)

**Запуск**:
```bash
pytest test_integration_scenarios.py -v
```

---

### 4. Тесты надежности (test_system_reliability.py)

**Проверяет**: Устойчивость к ошибкам

**Сценарии**:
- Пустой список инструментов
- Ошибки выполнения инструментов
- Некорректные коннекторы
- Очень длинный вход
- Параллельные выполнения
- Инструменты с нулевой репутацией
- Отсутствие промежуточных инструментов

**Запуск**:
```bash
pytest test_system_reliability.py -v
```

---

### 5. Тесты производительности (test_performance.py)

**Проверяет**: Скорость выполнения

**Сценарии**:
- Скорость Dijkstra
- Скорость Yen
- Скорость Softmax selector
- Скорость эмбеддингов
- Масштабируемость (10, 20, 50 инструментов)

**Запуск**:
```bash
pytest test_performance.py -v
```

---

## Запуск всех тестов

### Последовательный

```bash
cd examples/Tests/Functionals

# End-to-end
pytest test_e2e_workflow.py -v

# Integration
pytest test_integration_scenarios.py -v

# Reliability
pytest test_system_reliability.py -v

# Performance
pytest test_performance.py -v
```

### Все сразу

```bash
pytest -v
```

### С покрытием

```bash
pytest --cov=grapharchitect --cov-report=html
```

---

## Web API тесты

Требуют запущенный сервер:

```bash
# Терминал 1: Запустить сервер
cd src/GraphArchitectLib/Web
python main.py

# Терминал 2: Запустить тесты
cd examples/Tests/Functionals
pytest test_web_api.py -v
```

---

## Ожидаемые результаты

### Успешные тесты

```
test_e2e_workflow.py::TestEndToEndWorkflow::test_simple_classification_workflow PASSED
test_e2e_workflow.py::TestEndToEndWorkflow::test_multi_step_workflow PASSED
test_e2e_workflow.py::TestEndToEndWorkflow::test_training_updates_reputation PASSED
test_e2e_workflow.py::TestEndToEndWorkflow::test_temperature_decreases_with_experience PASSED
test_e2e_workflow.py::TestEndToEndWorkflow::test_no_path_found PASSED
test_e2e_workflow.py::TestEndToEndWorkflow::test_softmax_probabilities_valid PASSED

================================ 6 passed in 2.34s ================================
```

### Статистика

После запуска всех тестов:
```
======================== test session starts =========================
collected 25+ items

test_e2e_workflow.py ......                                      [ 24%]
test_integration_scenarios.py ....                               [ 40%]
test_system_reliability.py .......                               [ 68%]
test_performance.py .....                                        [100%]

======================== 25 passed in 5.67s ==========================
```

---

## Метрики качества

### Покрытие функциональности

| Компонент | Unit тесты | Functional тесты | Общее |
|-----------|------------|------------------|-------|
| Алгоритмы графа | 40 | 5 | 45 |
| Выбор инструментов | 22 | 8 | 30 |
| NLI | 26 | 3 | 29 |
| Execution | 24 | 12 | 36 |
| Training | 24 | 4 | 28 |
| Web API | - | 8 | 8 |

### Типы проверок

- **Корректность**: Алгоритмы работают правильно
- **Надежность**: Обработка ошибок
- **Производительность**: Скорость приемлема
- **Масштабируемость**: Работает с большими данными
- **Интеграция**: Компоненты работают вместе

---

## Требования

```bash
pip install pytest pytest-cov requests
```

---

## Структура

```
Functionals/
├── test_e2e_workflow.py           # E2E тесты (6 тестов)
├── test_web_api.py                # API тесты (8 тестов)
├── test_integration_scenarios.py  # Сценарии (4 теста)
├── test_system_reliability.py     # Надежность (7 тестов)
├── test_performance.py            # Производительность (5 тестов)
└── README.md                      # Эта документация
```

**Всего**: 30+ функциональных тестов

---

## Интерпретация результатов

### Все тесты прошли

Система готова к использованию:
- Все компоненты работают
- Обработка ошибок корректна
- Производительность приемлема

### Есть падающие тесты

Проверьте:
- Правильность конфигурации
- Доступность компонентов
- Логи для деталей

---

## Continuous Integration

Для CI/CD добавьте в `.github/workflows/tests.yml`:

```yaml
name: Functional Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run functional tests
        run: |
          cd examples/Tests/Functionals
          pytest -v --cov=grapharchitect
```

---

**Функциональные тесты готовы к запуску!**
