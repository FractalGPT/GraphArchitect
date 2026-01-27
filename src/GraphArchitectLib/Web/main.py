from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional
import aiofiles

# Импортируем API router
from api_router import api_router
from models import MessageRequest
from services import ChatService

# Импортируем WebSocket manager
import socketio
from websocket_manager import sio
from workflow_templates import get_all_templates
from agent_library import get_all_agents

app = FastAPI(
    title="Graph Architect", 
    description="Multi-Agent System with Dynamic Workflow and Competitive Agent Selection",
    version="3.0.0"
)

# CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API router
app.include_router(api_router)

# Настройка статики и шаблонов для GUI
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализируем сервисы
chat_service = ChatService()

# Доступные агенты для GUI
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
    """Главная страница - старый интерфейс"""
    templates_list = get_all_templates()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "agents": AVAILABLE_AGENTS,
        "templates": templates_list
    })


@app.get("/visualizer", response_class=HTMLResponse)
async def workflow_visualizer(request: Request):
    """Страница визуализации workflow с конкурентным выбором агентов"""
    return templates.TemplateResponse("workflow_view.html", {
        "request": request
    })


@app.get("/api/workflow-templates")
async def get_workflow_templates():
    """Получить список доступных шаблонов workflow"""
    return {"templates": get_all_templates()}


@app.get("/api/agents-library")
async def get_agents_library():
    """Получить библиотеку всех агентов"""
    agents = get_all_agents()
    return {
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "icon": agent.icon,
                "color": agent.color,
                "type": agent.type,
                "specialization": agent.specialization,
                "capabilities": agent.capabilities,
                "metrics": agent.metrics
            }
            for agent in agents
        ]
    }


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
async def chat_stream_gui(
        request: Request,
        message: str = Form(...),
        files: Optional[str] = Form(None)
):
    """Потоковый вывод для GUI (HTML формат)"""
    
    # Используем сервис для обработки
    file_list = json.loads(files) if files else []
    
    # Генерируем chat_id для GUI сессии (или получаем из сессии)
    chat_id = "gui_session_" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    msg_request = MessageRequest(
        chat_id=chat_id,
        message=message,
        files=[f["name"] for f in file_list] if file_list else []
    )

    async def generate():
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
        
        # Получаем стрим от сервиса и конвертируем в HTML
        async for chunk in chat_service.process_message_stream(msg_request):
            if chunk.type == "workflow":
                # Парсим workflow и отправляем только массив agents
                workflow_data = json.loads(chunk.content)
                agents_json = json.dumps(workflow_data.get('agents', []))
                yield f'<span data-workflow-agents=\'{agents_json}\' style="display:none;"></span>'
            
            elif chunk.type == "agent_start":
                # Маркер начала работы агента
                yield f'<span data-agent-start="{chunk.agent_id}" style="display:none;"></span>'
                yield f'<strong>{chunk.content}</strong><br><br>'
            
            elif chunk.type == "agent_complete":
                # Маркер завершения
                yield f'<span data-agent-complete="{chunk.agent_id}" style="display:none;"></span>'
            
            elif chunk.type == "text":
                # Текстовый контент
                yield chunk.content
        
        yield '</div></div>'

    return StreamingResponse(generate(), media_type="text/html")


# Оборачиваем FastAPI приложение в Socket.IO
# cors_allowed_origins='*' уже задано в websocket_manager.py
combined_asgi_app = socketio.ASGIApp(sio, app, socketio_path='/socket.io')

if __name__ == "__main__":
    import uvicorn
    import socket

    os.makedirs("uploads", exist_ok=True)
    
    # Функция для проверки доступности порта
    def is_port_available(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False
    
    # Ищем свободный порт
    port = 8000
    while not is_port_available(port) and port < 8010:
        print(f"[WARNING] Port {port} zaniat, probuem sleduyuschiy...")
        port += 1
    
    if port >= 8010:
        print("[ERROR] Ne udalos naiti svobodnyi port v diapazone 8000-8010")
        print("Ostanovite drugie protsessy ili izmenite port vruchnuyu")
    else:
        print(f"[OK] Zapusk servera na portu {port}")
        print(f"[WEB] Otkroite v brauzere: http://127.0.0.1:{port}")
        print(f"[API] API dokumentatsiya: http://127.0.0.1:{port}/docs")
        print(f"[WS] Socket.IO slushayet na /socket.io")
        uvicorn.run(combined_asgi_app, host="127.0.0.1", port=port, log_level="info")