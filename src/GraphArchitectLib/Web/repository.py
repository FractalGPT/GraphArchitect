"""
Repository layer for data operations.
For production, replace with real database (PostgreSQL, MongoDB, etc.)
"""
from typing import Dict, Optional, List
from datetime import datetime
from models import WorkflowChain, Agent, DocumentInfo, ChatInfo
import json
import os
import logging

logger = logging.getLogger(__name__)


class InMemoryRepository:
    """Simple in-memory storage (for development)."""
    
    def __init__(self):
        self._workflows: Dict[str, WorkflowChain] = {}
        self._documents: Dict[str, List[DocumentInfo]] = {}
        self._chats: Dict[str, ChatInfo] = {}
        self._agents: Dict[str, Agent] = {}
    
    # ============== Agent operations ==============
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents/tools."""
        return list(self._agents.values())
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get specific agent/tool by ID."""
        return self._agents.get(agent_id)
    
    def save_agent(self, agent: Agent) -> Agent:
        """Save agent/tool."""
        self._agents[agent.id] = agent
        return agent
        
    # ============== Работа с Workflow ==============
    
    def save_workflow(self, workflow: WorkflowChain) -> WorkflowChain:
        """Сохранить цепочку агентов"""
        self._workflows[workflow.chat_id] = workflow
        
        # Обновляем информацию о чате
        if workflow.chat_id in self._chats:
            self._chats[workflow.chat_id].workflow_chain = workflow
            self._chats[workflow.chat_id].last_activity = datetime.now()
        
        return workflow
    
    def get_workflow(self, chat_id: str) -> Optional[WorkflowChain]:
        """Получить цепочку агентов по ID чата"""
        return self._workflows.get(chat_id)
    
    def delete_workflow(self, chat_id: str) -> bool:
        """Удалить цепочку агентов"""
        if chat_id in self._workflows:
            del self._workflows[chat_id]
            return True
        return False
    
    # ============== Работа с документами ==============
    
    def save_document(self, document: DocumentInfo) -> DocumentInfo:
        """Сохранить информацию о документе"""
        if document.chat_id not in self._documents:
            self._documents[document.chat_id] = []
        
        self._documents[document.chat_id].append(document)
        
        # Обновляем информацию о чате
        if document.chat_id in self._chats:
            self._chats[document.chat_id].documents.append(document)
            self._chats[document.chat_id].last_activity = datetime.now()
        
        return document
    
    def get_documents(self, chat_id: str) -> List[DocumentInfo]:
        """Получить все документы чата"""
        return self._documents.get(chat_id, [])
    
    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Получить документ по ID"""
        for docs in self._documents.values():
            for doc in docs:
                if doc.document_id == document_id:
                    return doc
        return None
    
    # ============== Работа с чатами ==============
    
    def create_chat(self, chat_id: str, title: Optional[str] = None) -> ChatInfo:
        """Создать новый чат"""
        chat = ChatInfo(chat_id=chat_id, title=title)
        self._chats[chat_id] = chat
        return chat
    
    def get_chat(self, chat_id: str) -> Optional[ChatInfo]:
        """Получить информацию о чате"""
        return self._chats.get(chat_id)
    
    def update_chat_activity(self, chat_id: str):
        """Обновить время последней активности"""
        if chat_id in self._chats:
            self._chats[chat_id].last_activity = datetime.now()
    
    def list_chats(self) -> List[ChatInfo]:
        """Получить список всех чатов"""
        return list(self._chats.values())
    
    def delete_chat(self, chat_id: str) -> bool:
        """Удалить чат"""
        if chat_id in self._chats:
            # Удаляем связанные данные
            self._workflows.pop(chat_id, None)
            self._documents.pop(chat_id, None)
            del self._chats[chat_id]
            return True
        return False


class FileRepository(InMemoryRepository):
    """Хранилище с персистентностью в файлах"""
    
    def __init__(self, data_dir: str = "./data"):
        super().__init__()
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load data from files."""
        try:
            # Load workflows
            workflows_file = os.path.join(self.data_dir, "workflows.json")
            if os.path.exists(workflows_file):
                with open(workflows_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, workflow_data in data.items():
                        self._workflows[chat_id] = WorkflowChain(**workflow_data)
            
            # Load documents
            documents_file = os.path.join(self.data_dir, "documents.json")
            if os.path.exists(documents_file):
                with open(documents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, docs_data in data.items():
                        self._documents[chat_id] = [DocumentInfo(**doc) for doc in docs_data]
            
            # Load chats
            chats_file = os.path.join(self.data_dir, "chats.json")
            if os.path.exists(chats_file):
                with open(chats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, chat_data in data.items():
                        self._chats[chat_id] = ChatInfo(**chat_data)
            
            # Load agents (no agents in FileRepository - they should be in database)
            logger.info("FileRepository: agents should be loaded from SQLite database")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def _save_data(self):
        """Save data to files."""
        try:
            # Save workflows
            workflows_file = os.path.join(self.data_dir, "workflows.json")
            with open(workflows_file, 'w', encoding='utf-8') as f:
                data = {k: v.model_dump(mode='json') for k, v in self._workflows.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Save documents
            documents_file = os.path.join(self.data_dir, "documents.json")
            with open(documents_file, 'w', encoding='utf-8') as f:
                data = {k: [doc.model_dump(mode='json') for doc in v] 
                       for k, v in self._documents.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Save chats
            chats_file = os.path.join(self.data_dir, "chats.json")
            with open(chats_file, 'w', encoding='utf-8') as f:
                data = {k: v.model_dump(mode='json') for k, v in self._chats.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Note: agents should be in SQLite database, not files
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def save_workflow(self, workflow: WorkflowChain) -> WorkflowChain:
        result = super().save_workflow(workflow)
        self._save_data()
        return result
    
    def save_document(self, document: DocumentInfo) -> DocumentInfo:
        result = super().save_document(document)
        self._save_data()
        return result
    
    def create_chat(self, chat_id: str, title: Optional[str] = None) -> ChatInfo:
        result = super().create_chat(chat_id, title)
        self._save_data()
        return result
    
    def save_agent(self, agent: Agent) -> Agent:
        result = super().save_agent(agent)
        self._save_data()
        return result
    
    def delete_workflow(self, chat_id: str) -> bool:
        result = super().delete_workflow(chat_id)
        if result:
            self._save_data()
        return result
    
    def delete_chat(self, chat_id: str) -> bool:
        result = super().delete_chat(chat_id)
        if result:
            self._save_data()
        return result


# Singleton instance
_repository: Optional[InMemoryRepository] = None


def get_repository(use_file_storage: bool = True, use_sqlite: bool = True) -> InMemoryRepository:
    """
    Получить экземпляр repository.
    
    Args:
        use_file_storage: Использовать FileRepository (JSON файлы)
        use_sqlite: Использовать SQLite БД (рекомендуется)
    
    Returns:
        Repository instance
    
    Приоритет:
        1. SQLite (если use_sqlite=True) - РЕКОМЕНДУЕТСЯ
        2. FileRepository (если use_file_storage=True)
        3. InMemoryRepository (fallback)
    """
    global _repository
    
    if _repository is None:
        # Пробуем SQLite (лучший вариант)
        if use_sqlite:
            try:
                from sqlite_repository import get_sqlite_repository
                _repository = get_sqlite_repository()
                logger.info("Using SQLite repository")
                return _repository
            except Exception as e:
                logger.warning(f"SQLite not available ({e}), fallback to FileRepository")
        
        # Fallback на FileRepository
        if use_file_storage:
            _repository = FileRepository()
            logger.info("Using File repository (JSON)")
        else:
            _repository = InMemoryRepository()
            logger.warning("Using InMemory repository (data not persisted)")
    
    return _repository
