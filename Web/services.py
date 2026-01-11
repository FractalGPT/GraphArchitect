"""
Service слой с бизнес-логикой
"""
import asyncio
import uuid
from typing import AsyncGenerator, List, Optional
from datetime import datetime
import aiofiles
import os

from models import (
    Agent, WorkflowChain, MessageRequest, MessageChunk,
    DocumentInfo, WorkflowCreateRequest, WorkflowCreateResponse,
    MessageResponse
)
from repository import get_repository


# ============== Предустановленные агенты (для обратной совместимости) ==============

DEFAULT_AGENTS = {
    "text": [
        Agent(id="agent-researcher", name="Researcher", icon="🔍", color="#10b981", type="research", 
              specialization="Исследует данные", capabilities=["research", "data_collection"], metrics={}),
        Agent(id="agent-analyzer", name="Analyzer", icon="📊", color="#f59e0b", type="analysis",
              specialization="Анализирует информацию", capabilities=["analysis", "insights"], metrics={}),
        Agent(id="agent-writer", name="Writer", icon="✍️", color="#ec4899", type="writing",
              specialization="Генерирует текст", capabilities=["writing", "content_creation"], metrics={}),
        Agent(id="agent-reviewer", name="Reviewer", icon="✅", color="#ef4444", type="review",
              specialization="Проверяет качество", capabilities=["review", "quality_check"], metrics={})
    ],
    "image": [
        Agent(id="agent-image-analyzer", name="Image Analyzer", icon="🖼️", color="#10b981", type="image_processing",
              specialization="Анализ изображений", capabilities=["image_analysis", "vision"], metrics={}),
        Agent(id="agent-ocr", name="OCR", icon="📝", color="#f59e0b", type="text_extraction",
              specialization="Распознавание текста", capabilities=["ocr", "text_recognition"], metrics={}),
        Agent(id="agent-desc-generator", name="Description Generator", icon="✍️", color="#ec4899", type="description",
              specialization="Генерация описания", capabilities=["description", "captioning"], metrics={})
    ],
    "combined": [
        Agent(id="agent-content-analyzer", name="Content Analyzer", icon="🔍", color="#10b981", type="analysis",
              specialization="Анализ контента", capabilities=["content_analysis", "understanding"], metrics={}),
        Agent(id="agent-multimodal", name="Multimodal Processor", icon="🎨", color="#f59e0b", type="multimodal",
              specialization="Обработка мультимодальных данных", capabilities=["multimodal", "fusion"], metrics={}),
        Agent(id="agent-synthesizer", name="Synthesizer", icon="✍️", color="#ec4899", type="synthesis",
              specialization="Синтез ответа", capabilities=["synthesis", "integration"], metrics={}),
        Agent(id="agent-quality", name="Quality Check", icon="✅", color="#ef4444", type="quality_assurance",
              specialization="Проверка качества", capabilities=["qa", "validation"], metrics={})
    ]
}


class ChatService:
    """Сервис для работы с чатами и сообщениями"""
    
    def __init__(self):
        self.repo = get_repository()
    
    async def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowCreateResponse:
        """Создать цепочку агентов для чата"""
        
        # Определяем тип запроса
        request_type = request.request_type
        
        # Если файлы есть, может быть image или combined
        if request.files:
            # Проверяем типы файлов
            has_images = any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) 
                           for f in request.files)
            has_docs = any(f.lower().endswith(('.pdf', '.doc', '.docx', '.txt')) 
                          for f in request.files)
            
            if has_images and has_docs:
                request_type = "combined"
            elif has_images:
                request_type = "image"
            else:
                request_type = "combined"
        
        # Получаем подходящих агентов
        agents = DEFAULT_AGENTS.get(request_type, DEFAULT_AGENTS["text"])
        
        # Создаем workflow
        workflow = WorkflowChain(
            chat_id=request.chat_id,
            agents=agents,
            request_type=request_type
        )
        
        # Сохраняем в БД
        self.repo.save_workflow(workflow)
        
        # Создаем или обновляем чат
        existing_chat = self.repo.get_chat(request.chat_id)
        if not existing_chat:
            self.repo.create_chat(request.chat_id)
        
        return WorkflowCreateResponse(
            chat_id=request.chat_id,
            workflow=workflow,
            message=f"Created {request_type} workflow with {len(agents)} agents"
        )
    
    async def get_workflow(self, chat_id: str) -> Optional[WorkflowChain]:
        """Получить цепочку агентов для чата"""
        return self.repo.get_workflow(chat_id)
    
    async def process_message_stream(
        self, 
        request: MessageRequest
    ) -> AsyncGenerator[MessageChunk, None]:
        """Обработать сообщение со стримингом"""
        
        # Получаем workflow для чата
        workflow = self.repo.get_workflow(request.chat_id)
        
        if not workflow:
            # Создаем автоматически если нет
            create_req = WorkflowCreateRequest(
                chat_id=request.chat_id,
                request_type="text",
                user_message=request.message,
                files=request.files
            )
            workflow_resp = await self.create_workflow(create_req)
            workflow = workflow_resp.workflow
        
        # Отправляем информацию о workflow (только agents)
        import json
        agents_data = [agent.model_dump() for agent in workflow.agents]
        yield MessageChunk(
            type="workflow",
            content=json.dumps({"agents": agents_data}),
            metadata={"agents_count": len(workflow.agents)}
        )
        
        # Обрабатываем каждым агентом
        for agent in workflow.agents:
            # Начало работы агента
            yield MessageChunk(
                type="agent_start",
                content=f"{agent.icon} {agent.name}",
                agent_id=agent.id,
                metadata={"agent": agent.model_dump()}
            )
            
            await asyncio.sleep(0.1)
            
            # Процесс обработки
            work_msg = f'Обрабатываю запрос: <em>{request.message}</em><br>'
            if request.files and agent.id == 1:
                work_msg += f'Анализирую {len(request.files)} файл(ов)...<br>'
            
            # Стрим по словам
            words = work_msg.split(' ')
            for word in words:
                yield MessageChunk(
                    type="text",
                    content=word + ' '
                )
                await asyncio.sleep(0.05)
            
            await asyncio.sleep(0.3)
            
            # Результат агента
            result = f'✅ {agent.name} завершил анализ<br><br>'
            words = result.split(' ')
            for word in words:
                yield MessageChunk(
                    type="text",
                    content=word + ' '
                )
                await asyncio.sleep(0.05)
            
            # Завершение работы агента
            yield MessageChunk(
                type="agent_complete",
                content="",
                agent_id=agent.id
            )
            
            await asyncio.sleep(0.2)
        
        # Финальный ответ
        final = '---<br><br><strong>🎯 Итоговый результат</strong><br><br>'
        final += f'Ваш запрос «{request.message}» был успешно обработан всей цепочкой агентов.<br><br>'
        if request.files:
            final += f'📎 Проанализировано файлов: {len(request.files)}<br>'
        final += '🔍 Исследование завершено<br>'
        final += '📊 Данные проанализированы<br>'
        final += '✍️ Текст сгенерирован<br>'
        final += '✅ Качество проверено<br><br>'
        final += 'Система готова к следующему запросу.'
        
        words = final.split(' ')
        for word in words:
            yield MessageChunk(
                type="text",
                content=word + ' '
            )
            await asyncio.sleep(0.03)
    
    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """Обработать сообщение без стриминга"""
        
        start_time = datetime.now()
        
        # Получаем workflow
        workflow = self.repo.get_workflow(request.chat_id)
        if not workflow:
            create_req = WorkflowCreateRequest(
                chat_id=request.chat_id,
                request_type="text",
                user_message=request.message,
                files=request.files
            )
            workflow_resp = await self.create_workflow(create_req)
            workflow = workflow_resp.workflow
        
        # Имитация обработки
        await asyncio.sleep(1)
        
        # Формируем ответ
        response_text = f"Обработано {len(workflow.agents)} агентами. Результат готов."
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return MessageResponse(
            chat_id=request.chat_id,
            message=request.message,
            response_type="text",
            response_data=response_text,
            workflow_used=workflow.agents,
            processing_time=processing_time
        )


class DocumentService:
    """Сервис для работы с документами"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.repo = get_repository()
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    async def save_document(
        self, 
        chat_id: str, 
        file: bytes,
        filename: str,
        content_type: str
    ) -> DocumentInfo:
        """Сохранить документ"""
        
        # Генерируем уникальный ID
        document_id = str(uuid.uuid4())
        
        # Сохраняем файл
        file_ext = os.path.splitext(filename)[1]
        saved_filename = f"{document_id}{file_ext}"
        file_path = os.path.join(self.upload_dir, saved_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file)
        
        # Создаем запись в БД
        document = DocumentInfo(
            document_id=document_id,
            chat_id=chat_id,
            filename=filename,
            content_type=content_type,
            size=len(file),
            path=file_path
        )
        
        self.repo.save_document(document)
        
        # Создаем чат если не существует
        if not self.repo.get_chat(chat_id):
            self.repo.create_chat(chat_id)
        
        return document
    
    async def get_documents(self, chat_id: str) -> List[DocumentInfo]:
        """Получить все документы чата"""
        return self.repo.get_documents(chat_id)
    
    async def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Получить информацию о документе"""
        return self.repo.get_document(document_id)
