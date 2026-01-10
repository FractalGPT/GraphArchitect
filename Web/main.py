from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional
import aiofiles

app = FastAPI(title="Graph Architect")

# Настройка статики и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Хранилище сессий (в production использовать Redis/DB)
sessions = {}

# Агенты системы
AGENTS = [
    {"id": 1, "name": "Researcher", "icon": "🔍", "color": "#10b981"},
    {"id": 2, "name": "Analyzer", "icon": "📊", "color": "#f59e0b"},
    {"id": 3, "name": "Writer", "icon": "✍️", "color": "#ec4899"},
    {"id": 4, "name": "Reviewer", "icon": "✅", "color": "#ef4444"}
]

AVAILABLE_AGENTS = [
    {"name": "Deep Research", "avatar": "🔬", "color": "#10b981", "desc": "Доступен"},
    {"name": "Marketing AI", "avatar": "📈", "color": "#f59e0b", "desc": "Доступен"},
    {"name": "Physics Agent", "avatar": "⚛️", "color": "#ec4899", "desc": "Доступен"},
    {"name": "Medical Agent", "avatar": "🏥", "color": "#ef4444", "desc": "Доступен"},
    {"name": "General Agent", "avatar": "🤖", "color": "#6366f1", "desc": "Доступен"}
]


def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} ТБ"


def get_file_icon(filename: str) -> str:
    """Получение иконки по типу файла"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        '.pdf': '📕',
        '.doc': '📘', '.docx': '📘',
        '.txt': '📄',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp3': '🎵', '.wav': '🎵', '.m4a': '🎵',
        '.zip': '🗜️', '.rar': '🗜️', '.7z': '🗜️'
    }
    return icons.get(ext, '📎')


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "agents": AVAILABLE_AGENTS
    })


@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Загрузка файлов"""
    uploaded = []

    for file in files:
        # Сохранение файла (в production использовать постоянное хранилище)
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        uploaded.append({
            "name": file.filename,
            "size": len(content),
            "icon": get_file_icon(file.filename)
        })

    # Генерация HTML для отображения файлов
    html = ""
    for file_info in uploaded:
        html += f"""
        <div class="file-item">
            <div class="file-icon">{file_info['icon']}</div>
            <div class="file-details">
                <div class="file-name">{file_info['name']}</div>
                <div class="file-size">{format_file_size(file_info['size'])}</div>
            </div>
        </div>
        """

    if html:
        return HTMLResponse(f'<div class="uploaded-files-container">{html}</div>')
    return HTMLResponse("")


@app.post("/chat/stream")
async def chat_stream(
        request: Request,
        message: str = Form(...),
        files: Optional[str] = Form(None)
):
    """Потоковый вывод ответа от агентов"""

    async def generate():
        # Парсинг информации о файлах
        file_list = json.loads(files) if files else []

        # Начальное сообщение с файлами
        if file_list:
            yield '<div class="message assistant-message">'
            yield '<div class="message-content">'
            yield '<strong>📎 Загруженные файлы:</strong><br><br>'
            for file_info in file_list:
                yield f'- {file_info["icon"]} {file_info["name"]} ({format_file_size(file_info["size"])})<br>'
            yield '<br>---<br><br>'
        else:
            yield '<div class="message assistant-message"><div class="message-content">'

        await asyncio.sleep(0.1)
        completed = []

        # Обработка каждым агентом
        for agent in AGENTS:
            # Маркер начала работы агента (для JS)
            yield f'<span data-agent-start="{agent["id"]}" style="display:none;"></span>'

            # Сообщение агента
            yield f'<strong>{agent["icon"]} {agent["name"]}</strong><br><br>'
            await asyncio.sleep(0.1)

            # Процесс обработки
            work_msg = f'Обрабатываю запрос: <em>{message}</em><br>'
            if file_list and agent['id'] == 1:
                work_msg += f'Анализирую {len(file_list)} файл(ов)...<br>'

            # Потоковый вывод текста по словам
            words = work_msg.split(' ')
            for word in words:
                yield word + ' '
                await asyncio.sleep(0.05)

            await asyncio.sleep(0.3)

            # Результат агента
            result = f'✅ {agent["name"]} завершил анализ<br><br>'
            words = result.split(' ')
            for word in words:
                yield word + ' '
                await asyncio.sleep(0.05)

            # Маркер завершения работы агента (для JS)
            yield f'<span data-agent-complete="{agent["id"]}" style="display:none;"></span>'
            await asyncio.sleep(0.2)

        # Финальный ответ
        final = '---<br><br><strong>🎯 Итоговый результат</strong><br><br>'
        final += f'Ваш запрос «{message}» был успешно обработан всей цепочкой агентов.<br><br>'
        if file_list:
            final += f'📎 Проанализировано файлов: {len(file_list)}<br>'
        final += '🔍 Исследование завершено<br>'
        final += '📊 Данные проанализированы<br>'
        final += '✍️ Текст сгенерирован<br>'
        final += '✅ Качество проверено<br><br>'
        final += 'Система готова к следующему запросу.'

        # Потоковый вывод финального сообщения
        words = final.split(' ')
        for word in words:
            yield word + ' '
            await asyncio.sleep(0.03)

        yield '</div></div>'

    return StreamingResponse(generate(), media_type="text/html")


if __name__ == "__main__":
    import uvicorn

    os.makedirs("uploads", exist_ok=True)
    uvicorn.run(app, host="127.0.0.1", port=8000)