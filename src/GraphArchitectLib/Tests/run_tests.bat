@echo off
REM Скрипт для запуска тестов GraphArchitect на Windows

setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo   ЗАПУСК ТЕСТОВ GRAPHARCHITECT
echo ====================================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.8+
    exit /b 1
)

REM Проверка наличия pytest
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [УСТАНОВКА] Устанавливаем pytest...
    pip install -r requirements-test.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        exit /b 1
    )
)

REM Выбор режима запуска
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help
if "%1"=="--list" goto :list
if "%1"=="-l" goto :list

if "%1"=="" (
    echo [РЕЖИМ] Все тесты
    pytest -v --tb=short
    goto :end
)

if "%1"=="--fast" (
    echo [РЕЖИМ] Быстрые тесты
    pytest -v --tb=short -m "not slow"
    goto :end
)

if "%1"=="--coverage" (
    echo [РЕЖИМ] С покрытием кода
    pytest -v --tb=short --cov=grapharchitect --cov-report=html --cov-report=term-missing
    echo.
    echo [INFO] HTML отчет: htmlcov\index.html
    goto :end
)

if "%1"=="--selection" (
    echo [РЕЖИМ] Тесты selection (ключевой модуль!)
    pytest test_selection.py -v --tb=short
    goto :end
)

if "%1"=="--graph" (
    echo [РЕЖИМ] Тесты алгоритмов графа
    pytest test_graph_algorithms.py -v --tb=short
    goto :end
)

if "%1"=="--entities" (
    echo [РЕЖИМ] Тесты сущностей
    pytest test_entities.py -v --tb=short
    goto :end
)

if "%1"=="--services" (
    echo [РЕЖИМ] Тесты сервисов
    pytest test_services.py -v --tb=short
    goto :end
)

if "%1"=="--execution" (
    echo [РЕЖИМ] Тесты выполнения и обучения
    pytest test_execution_training.py -v --tb=short
    goto :end
)

if "%1"=="--nli" (
    echo [РЕЖИМ] Тесты NLI
    pytest test_nli.py -v --tb=short
    goto :end
)

if "%1"=="--parallel" (
    echo [РЕЖИМ] Параллельное выполнение
    pytest -v --tb=short -n auto
    goto :end
)

echo [ОШИБКА] Неизвестный параметр: %1
echo Используйте --help для справки
goto :end

:help
echo.
echo ИСПОЛЬЗОВАНИЕ: run_tests.bat [опция]
echo.
echo ОПЦИИ:
echo   (пусто)        Запустить все тесты
echo   --fast         Только быстрые тесты
echo   --coverage     С измерением покрытия кода
echo   --parallel     Параллельное выполнение
echo.
echo   --selection    Тесты selection (ключевой модуль!)
echo   --graph        Тесты алгоритмов графа
echo   --entities     Тесты сущностей
echo   --services     Тесты сервисов
echo   --execution    Тесты выполнения и обучения
echo   --nli          Тесты NLI
echo.
echo   --list         Показать список тестов
echo   --help         Показать эту справку
echo.
echo ПРИМЕРЫ:
echo   run_tests.bat
echo   run_tests.bat --fast
echo   run_tests.bat --coverage
echo   run_tests.bat --selection
echo.
goto :end

:list
echo.
echo ДОСТУПНЫЕ ТЕСТЫ:
echo.
if exist test_graph_algorithms.py (
    echo   [OK] test_graph_algorithms.py  - Алгоритмы графа
) else (
    echo   [  ] test_graph_algorithms.py  - НЕ НАЙДЕН
)
if exist test_entities.py (
    echo   [OK] test_entities.py          - Сущности
) else (
    echo   [  ] test_entities.py          - НЕ НАЙДЕН
)
if exist test_selection.py (
    echo   [OK] test_selection.py         - Выбор инструментов (ключевой!)
) else (
    echo   [  ] test_selection.py         - НЕ НАЙДЕН
)
if exist test_services.py (
    echo   [OK] test_services.py          - Сервисы
) else (
    echo   [  ] test_services.py          - НЕ НАЙДЕН
)
if exist test_execution_training.py (
    echo   [OK] test_execution_training.py - Выполнение и обучение
) else (
    echo   [  ] test_execution_training.py - НЕ НАЙДЕН
)
if exist test_nli.py (
    echo   [OK] test_nli.py               - NLI
) else (
    echo   [  ] test_nli.py               - НЕ НАЙДЕН
)
echo.
goto :end

:end
echo.
echo ====================================================================
endlocal
