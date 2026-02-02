@echo off
echo ======================================================================
echo GraphArchitect - Функциональные тесты
echo ======================================================================
echo.

set PYTHON=C:\Users\ZZZ\AppData\Local\Programs\Python\Python310\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python не найден
    pause
    exit /b 1
)

echo Запуск всех функциональных тестов...
echo.

echo [1/5] End-to-End Workflow тесты
echo ======================================================================
"%PYTHON%" -m pytest test_e2e_workflow.py -v --tb=short
if errorlevel 1 (
    echo [FAILED] E2E тесты провалились
    pause
    exit /b 1
)
echo.
pause

echo.
echo [2/5] Web API тесты
echo ======================================================================
echo [WARNING] Требуется запущенный сервер (python main.py)
echo.
pause

"%PYTHON%" -m pytest test_web_api.py -v --tb=short
if errorlevel 1 (
    echo [WARNING] Web API тесты провалились (сервер запущен?)
)
echo.
pause

echo.
echo [3/5] Integration Scenarios тесты
echo ======================================================================
"%PYTHON%" -m pytest test_integration_scenarios.py -v --tb=short
if errorlevel 1 (
    echo [FAILED] Integration тесты провалились
    pause
    exit /b 1
)
echo.
pause

echo.
echo [4/5] System Reliability тесты
echo ======================================================================
"%PYTHON%" -m pytest test_system_reliability.py -v --tb=short
if errorlevel 1 (
    echo [FAILED] Reliability тесты провалились
    pause
    exit /b 1
)
echo.
pause

echo.
echo [5/5] Performance тесты
echo ======================================================================
"%PYTHON%" -m pytest test_performance.py -v --tb=short
if errorlevel 1 (
    echo [WARNING] Performance тесты провалились
)
echo.

echo ======================================================================
echo ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ ЗАВЕРШЕНЫ
echo ======================================================================
echo.
echo Результаты:
echo   - E2E Workflow: Проверка полного цикла
echo   - Web API: Проверка endpoints
echo   - Integration: Проверка сценариев
echo   - Reliability: Проверка устойчивости
echo   - Performance: Проверка скорости
echo.
echo Для детального отчета используйте:
echo   pytest -v --cov=grapharchitect --cov-report=html
echo.
pause
