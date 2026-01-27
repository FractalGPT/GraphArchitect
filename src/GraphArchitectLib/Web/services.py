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
    
    async def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowChain:
        """Создать цепочку агентов для чата (Генерация графа)"""
        from workflow_templates import get_workflow_template
        
        # Выбираем алгоритм
        workflow = get_workflow_template(request.planning_algorithm) or get_workflow_template("yen_5")
        
        workflow.chat_id = request.chat_id
        workflow.files = request.files or []
        
        # Сохраняем в БД
        self.repo.save_workflow(workflow)
        
        return workflow
    
    async def get_workflow(self, chat_id: str) -> Optional[WorkflowChain]:
        """Получить цепочку агентов для чата"""
        return self.repo.get_workflow(chat_id)
    
    async def generate_graph_architecture_stream(self, request: WorkflowCreateRequest) -> AsyncGenerator[MessageChunk, None]:
        """Стримминг этапов проектирования графа"""
        from workflow_templates import get_workflow_template
        
        workflow = get_workflow_template(request.planning_algorithm) or get_workflow_template("yen_5")
        
        # Инфо о воркфлоу
        yield MessageChunk(
            type="workflow_info",
            metadata={
                "name": workflow.name,
                "steps": [{"id": s.id, "name": s.name} for s in workflow.steps]
            }
        )

        top_k = 5
        if "3" in workflow.name: top_k = 3
        elif "10" in workflow.name: top_k = 10

        phases = [
            ("knn", "Поиск архитектур в k-NN..."),
            ("graph_algo", f"Генерация {top_k} вариантов ({workflow.name})"),
            ("llm_refine", f"LLM-синтез из Top-{top_k} путей")
        ]

        for phase_id, phase_name in phases:
            yield MessageChunk(type="gen_phase_start", phase_id=phase_id, content=phase_name)
            for i in range(5):
                await asyncio.sleep(0.3)
                yield MessageChunk(type="gen_progress", phase_id=phase_id, progress=(i+1)*20)
            yield MessageChunk(type="gen_phase_complete", phase_id=phase_id)
            await asyncio.sleep(0.2)

    async def process_full_workflow_stream(self, request: MessageRequest) -> AsyncGenerator[MessageChunk, None]:
        """Полный цикл работы через стриминг: Проектирование -> Выбор -> Выполнение"""
        print(f"DEBUG: Processing workflow with algorithm: {request.planning_algorithm}")
        from workflow_templates import get_workflow_template
        import random

        # 1. ПОДГОТОВКА (Генерация архитектуры через новый метод)
        async for chunk in self.generate_graph_architecture_stream(
            WorkflowCreateRequest(
                chat_id=request.chat_id, 
                user_message=request.message, 
                planning_algorithm=request.planning_algorithm,
                request_type="text",
                files=request.files
            )
        ):
            yield chunk

        # Получаем workflow для выполнения
        workflow = get_workflow_template(request.planning_algorithm) or get_workflow_template("yen_5")
        print(f"DEBUG: Selected template name: {workflow.name}")
        
        await asyncio.sleep(0.5)

        # 3. ВЫПОЛНЕНИЕ ШАГОВ (Выбор + Запуск)
        from agent_library import get_agent
        for step in workflow.steps:
            # СТАРТ ШАГА
            yield MessageChunk(
                type="step_started", 
                step_id=step.id, 
                metadata={"name": step.name, "candidates": step.candidate_agents}
            )
            await asyncio.sleep(0.3)

            # ВЫБОР АГЕНТА (Competition)
            candidates = [get_agent(aid) for aid in step.candidate_agents if get_agent(aid)]
            scores = {c.id: 0 for c in candidates}
            
            # Ускоренный выбор (теперь ~1.2 сек вместо 3 сек, но с сохранением видимости прогресса)
            for p in range(0, 101, 10): # Больше промежуточных кадров (10 вместо 20)
                await asyncio.sleep(0.12) 
                for c in candidates:
                    # Имитируем рост уверенности агента
                    scores[c.id] = round(random.uniform(0.6, 0.95) if p < 80 else random.uniform(0.85, 0.99), 3)
                    yield MessageChunk(type="agent_progress", agent_id=c.id, progress=p, step_id=step.id)
                
                yield MessageChunk(
                    type="agent_score_updated", 
                    step_id=step.id,
                    metadata={"agents": [{"agentId": cid, "score": s} for cid, s in scores.items()]}
                )

            winner = max(candidates, key=lambda c: scores[c.id])
            yield MessageChunk(type="agent_selected", agent_id=winner.id, step_id=step.id, score=scores[winner.id])
            
            await asyncio.sleep(0.8) # Важная пауза: дать пользователю увидеть победителя

            # ИСПОЛНЕНИЕ АГЕНТОМ
            actions = ["Анализ контекста...", "Генерация решения...", "Проверка результата..."]
            for i, action in enumerate(actions):
                await asyncio.sleep(0.5) # Чуть медленнее выполнение для солидности
                progress = int(((i+1)/len(actions))*100)
                yield MessageChunk(type="agent_executing", agent_id=winner.id, step_id=step.id, progress=progress, content=action)

            yield MessageChunk(type="step_completed", step_id=step.id)
            await asyncio.sleep(0.4) # Пауза перед следующим шагом графа

        # 4. ФИНАЛЬНЫЙ ТЕКСТ
        final_text = f"🎯 Граф успешно выполнен с помощью алгоритма {workflow.name}."
        yield MessageChunk(type="text", content=final_text)
    
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
