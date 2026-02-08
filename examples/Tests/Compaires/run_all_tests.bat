@echo off
echo ======================================================================
echo GraphArchitect - Сравнительные тесты
echo ======================================================================
echo.

set PYTHON=C:\Users\ZZZ\AppData\Local\Programs\Python\Python310\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python не найден: %PYTHON%
    pause
    exit /b 1
)

echo Запуск всех сравнительных тестов...
echo.

rem Тест 1: Датасет
echo [1/3] Проверка датасета задач
echo ======================================================================
"%PYTHON%" test_tasks_dataset.py
if errorlevel 1 (
    echo [ERROR] Ошибка в датасете
    pause
    exit /b 1
)
echo.
echo [OK] Датасет готов: 50 задач
echo.
pause

rem Тест 2: Сравнение с LlamaIndex
echo.
echo [2/3] Сравнение с LlamaIndex Workflow
echo ======================================================================
"%PYTHON%" benchmark_vs_llamaindex.py
if errorlevel 1 (
    echo [ERROR] Ошибка в тесте
    pause
    exit /b 1
)
echo.
echo [OK] Тест завершен - см. benchmark_results.json
echo.
pause

rem Тест 3: RLAIF улучшение
echo.
echo [3/3] Измерение RLAIF улучшения
echo ======================================================================

if not defined OPENROUTER_API_KEY (
    echo [WARNING] OPENROUTER_API_KEY не установлен
    echo Тест будет использовать симуляцию оценок
    echo.
    echo Для реальных измерений:
    echo   set OPENROUTER_API_KEY=your-key
    echo.
    pause
)

"%PYTHON%" benchmark_rlaif_improvement.py
if errorlevel 1 (
    echo [ERROR] Ошибка в тесте
    pause
    exit /b 1
)
echo.
echo [OK] Тест завершен - см. rlaif_improvement_results.json
echo.

echo ======================================================================
echo ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ
echo ======================================================================
echo.
echo Результаты:
echo   1. benchmark_results.json - сравнение с LlamaIndex
echo   2. rlaif_improvement_results.json - улучшение через RLAIF
echo.
echo Проверьте improvement_percent в файлах результатов.
echo.
echo Требования ТЗ:
echo   - +100%% больше задач: см. benchmark_results.json
echo   - +30%% по RLAIF: см. rlaif_improvement_results.json
echo.
pause
