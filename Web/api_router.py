"""
API Router - Чистое REST API
Может использоваться независимо от GUI
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json

from models import (
    MessageRequest, MessageResponse, WorkflowCreateRequest,
    WorkflowCreateResponse, WorkflowChain, DocumentInfo,
    ApiResponse, ErrorResponse, ChatInfo
)
from services import ChatService, DocumentService


# Создаем роутер
api_router = APIRouter(prefix="/api", tags=["api"])

# Инициализируем сервисы
chat_service = ChatService()
document_service = DocumentService()


# ============== Workflow endpoints ==============

@api_router.post("/chat/{chat_id}/workflow", response_model=WorkflowCreateResponse)
async def create_workflow(
    chat_id: str,
    request_type: str = Form(...),
    user_message: str = Form(...),
    files: Optional[List[str]] = Form(None)
):
    """
    Создать цепочку агентов для чата
    
    **Параметры:**
    - chat_id: ID чата
    - request_type: Тип запроса (text/image/combined)
    - user_message: Сообщение пользователя
    - files: Список файлов (опционально)
    
    **Возвращает:**
    - WorkflowCreateResponse с созданной цепочкой агентов
    """
    try:
        req = WorkflowCreateRequest(
            chat_id=chat_id,
            request_type=request_type,  # type: ignore
            user_message=user_message,
            files=files or []
        )
        
        workflow = await chat_service.create_workflow(req)
        return workflow
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating workflow: {str(e)}"
        )


@api_router.get("/chat/{chat_id}/workflow", response_model=WorkflowChain)
async def get_workflow(chat_id: str):
    """
    Получить цепочку агентов для чата
    
    **Параметры:**
    - chat_id: ID чата
    
    **Возвращает:**
    - WorkflowChain - цепочка агентов
    
    **Ошибки:**
    - 404: Workflow не найден
    """
    workflow = await chat_service.get_workflow(chat_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found for chat_id: {chat_id}"
        )
    
    return workflow


# ============== Message endpoints ==============

@api_router.post("/chat/{chat_id}/message/stream")
async def send_message_stream(
    chat_id: str,
    message: str = Form(...),
    files: Optional[str] = Form(None)
):
    """
    Отправить сообщение с потоковым ответом
    
    **Параметры:**
    - chat_id: ID чата
    - message: Текст сообщения
    - files: JSON со списком файлов (опционально)
    
    **Возвращает:**
    - StreamingResponse с чанками ответа
    
    **Примечание:**
    - Цепочка агентов подтягивается из БД по chat_id
    - Если цепочки нет, создается автоматически
    """
    try:
        file_list = json.loads(files) if files else []
        
        request = MessageRequest(
            chat_id=chat_id,
            message=message,
            files=file_list
        )
        
        async def generate():
            async for chunk in chat_service.process_message_stream(request):
                # Форматируем в JSON + newline для стриминга
                yield chunk.model_dump_json() + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",  # Newline Delimited JSON
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@api_router.post("/chat/{chat_id}/message", response_model=MessageResponse)
async def send_message(
    chat_id: str,
    message: str = Form(...),
    files: Optional[List[str]] = Form(None)
):
    """
    Отправить сообщение без стриминга
    
    **Параметры:**
    - chat_id: ID чата
    - message: Текст сообщения
    - files: Список файлов (опционально)
    
    **Возвращает:**
    - MessageResponse с полным ответом
    
    **Примечание:**
    - Цепочка агентов подтягивается из БД по chat_id
    - Если цепочки нет, создается автоматически
    """
    try:
        request = MessageRequest(
            chat_id=chat_id,
            message=message,
            files=files or []
        )
        
        response = await chat_service.process_message(request)
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


# ============== Document endpoints ==============

@api_router.post("/chat/{chat_id}/document", response_model=DocumentInfo)
async def upload_document(
    chat_id: str,
    file: UploadFile = File(...)
):
    """
    Загрузить документ в чат
    
    **Параметры:**
    - chat_id: ID чата
    - file: Файл для загрузки
    
    **Возвращает:**
    - DocumentInfo с информацией о сохраненном документе
    
    **Примечание:**
    - Документ сохраняется в файловую систему
    - Метаданные сохраняются в БД
    """
    try:
        content = await file.read()
        
        document = await document_service.save_document(
            chat_id=chat_id,
            file=content,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream"
        )
        
        return document
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@api_router.get("/chat/{chat_id}/documents", response_model=List[DocumentInfo])
async def get_documents(chat_id: str):
    """
    Получить все документы чата
    
    **Параметры:**
    - chat_id: ID чата
    
    **Возвращает:**
    - List[DocumentInfo] со списком документов
    """
    documents = await document_service.get_documents(chat_id)
    return documents


@api_router.get("/document/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """
    Получить информацию о документе
    
    **Параметры:**
    - document_id: ID документа
    
    **Возвращает:**
    - DocumentInfo с информацией о документе
    
    **Ошибки:**
    - 404: Документ не найден
    """
    document = await document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}"
        )
    
    return document


# ============== Chat endpoints ==============

@api_router.get("/chat/{chat_id}", response_model=ChatInfo)
async def get_chat_info(chat_id: str):
    """
    Получить информацию о чате
    
    **Параметры:**
    - chat_id: ID чата
    
    **Возвращает:**
    - ChatInfo с полной информацией о чате
    
    **Ошибки:**
    - 404: Чат не найден
    """
    repo = chat_service.repo
    chat = repo.get_chat(chat_id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat not found: {chat_id}"
        )
    
    return chat


@api_router.get("/chats", response_model=List[ChatInfo])
async def list_chats():
    """
    Получить список всех чатов
    
    **Возвращает:**
    - List[ChatInfo] со списком всех чатов
    """
    repo = chat_service.repo
    chats = repo.list_chats()
    return chats


@api_router.delete("/chat/{chat_id}", response_model=ApiResponse)
async def delete_chat(chat_id: str):
    """
    Удалить чат и все связанные данные
    
    **Параметры:**
    - chat_id: ID чата
    
    **Возвращает:**
    - ApiResponse с результатом операции
    """
    repo = chat_service.repo
    success = repo.delete_chat(chat_id)
    
    if success:
        return ApiResponse(
            success=True,
            message=f"Chat {chat_id} deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat not found: {chat_id}"
        )


# ============== Health check ==============

@api_router.get("/health", response_model=ApiResponse)
async def health_check():
    """
    Проверка работоспособности API
    
    **Возвращает:**
    - ApiResponse со статусом API
    """
    return ApiResponse(
        success=True,
        message="API is healthy",
        data={"version": "1.0.0", "status": "online"}
    )
