"""
Модели данных для API
"""
from typing import List, Optional, Union, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============== Модели агентов ==============

class Agent(BaseModel):
    """Агент в цепочке обработки"""
    id: str
    name: str
    icon: str
    color: str
    type: str = "general"
    specialization: Optional[str] = None
    capabilities: List[str] = []
    metrics: Dict[str, Any] = {}


class CandidateProgress(BaseModel):
    """Прогресс кандидата в конкурентном выборе"""
    agent_id: str
    status: Literal["competing", "leading", "eliminated", "winner"] = "competing"
    progress: int = 0  # 0-100
    score: Optional[float] = None  # 0.0-1.0


class SelectionCriteria(BaseModel):
    """Критерии выбора агента"""
    strategy: Literal["fastest_response", "best_quality_score", "consensus", "balanced"] = "best_quality_score"
    timeout: int = 10000  # миллисекунды


class WorkflowStep(BaseModel):
    """Шаг в workflow (внутри шага выбирается 1 из N агентов)"""
    id: str
    name: str
    order: int
    description: Optional[str] = None
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    phase: Optional[Literal["selection", "executing", "completed"]] = None
    
    # Агенты-кандидаты для этого шага (выбирается 1 из N)
    candidate_agents: List[str] = Field(default_factory=list, alias="candidateAgents")
    
    # Выбранный агент (после конкурентного отбора)
    selected_agent_id: Optional[str] = Field(default=None, alias="selectedAgentId")
    
    # Критерии выбора агента
    selection_criteria: SelectionCriteria = Field(default_factory=SelectionCriteria, alias="selectionCriteria")
    
    # Прогресс кандидатов (для real-time обновлений)
    candidates_progress: List[CandidateProgress] = Field(default_factory=list, alias="candidatesProgress")
    
    # Результат выполнения
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class WorkflowChain(BaseModel):
    """Цепочка шагов для обработки (шаги выполняются последовательно)"""
    chat_id: str
    name: str = "Default Workflow"
    description: Optional[str] = None
    
    # Шаги выполняются последовательно
    steps: List[WorkflowStep] = []
    
    # Индекс текущего шага
    current_step_index: int = Field(default=0, alias="currentStepIndex")
    
    created_at: datetime = Field(default_factory=datetime.now)
    request_type: Literal["text", "image", "combined"] = "text"
    
    # Старый формат для обратной совместимости
    agents: List[Agent] = []
    
    class Config:
        populate_by_name = True


# ============== Модели сообщений ==============

class MessageRequest(BaseModel):
    """Запрос на отправку сообщения"""
    chat_id: str
    message: str
    files: Optional[List[str]] = []


class MessageChunk(BaseModel):
    """Чанк ответа (для стриминга)"""
    type: Literal["text", "agent_start", "agent_complete", "workflow", "image", "document"]
    content: str
    agent_id: Optional[str] = None  # Изменено на str для совместимости с новыми ID
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    """Полный ответ на сообщение"""
    chat_id: str
    message: str
    response_type: Literal["text", "image", "document", "combined"]
    response_data: Union[str, dict]
    workflow_used: List[Agent]
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)


# ============== Модели документов ==============

class DocumentUpload(BaseModel):
    """Загрузка документа"""
    chat_id: str
    filename: str
    content_type: str
    size: int


class DocumentInfo(BaseModel):
    """Информация о сохраненном документе"""
    document_id: str
    chat_id: str
    filename: str
    content_type: str
    size: int
    path: str
    uploaded_at: datetime = Field(default_factory=datetime.now)


# ============== Модели создания workflow ==============

class WorkflowCreateRequest(BaseModel):
    """Запрос на создание цепочки агентов"""
    chat_id: str
    request_type: Literal["text", "image", "combined"]
    user_message: str
    files: Optional[List[str]] = []


class WorkflowCreateResponse(BaseModel):
    """Ответ с созданной цепочкой"""
    chat_id: str
    workflow: WorkflowChain
    message: str = "Workflow created successfully"


# ============== Модели чата ==============

class ChatInfo(BaseModel):
    """Информация о чате"""
    chat_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    workflow_chain: Optional[WorkflowChain] = None
    documents: List[DocumentInfo] = []


# ============== Модели ответа API ==============

class ApiResponse(BaseModel):
    """Стандартный ответ API"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
