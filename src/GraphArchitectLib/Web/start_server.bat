@echo off
REM Скрипт запуска Web API с проверкой интеграции GraphArchitect

setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo   GRAPH ARCHITECT WEB API - ЗАПУСК
echo ====================================================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.8+
    exit /b 1
)

REM Установка зависимостей
echo [1/3] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo   Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo   [ОШИБКА] Не удалось установить зависимости
        exit /b 1
    )
)
echo   ✓ Зависимости установлены

echo.
echo [2/3] Проверка интеграции GraphArchitect...
python check_integration.py
if errorlevel 1 (
    echo.
    echo [ВНИМАНИЕ] Интеграция не полностью работает
    echo Сервер будет работать в режиме симуляции
    echo.
    timeout /t 3 >nul
)

echo.
echo [3/3] Запуск сервера...
echo.
echo ====================================================================
echo   ✓ Сервер запускается...
echo   
echo   Web Interface: http://127.0.0.1:8000
echo   Visualizer:    http://127.0.0.1:8000/visualizer
echo   API Docs:      http://127.0.0.1:8000/docs
echo   Health Check:  http://127.0.0.1:8000/api/health
echo ====================================================================
echo.

python main.py

endlocal
