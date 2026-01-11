"""
Repository слой для работы с данными
В production заменить на реальную БД (PostgreSQL, MongoDB, etc.)
"""
from typing import Dict, Optional, List
from datetime import datetime
from models import WorkflowChain, Agent, DocumentInfo, ChatInfo
import json
import os


class InMemoryRepository:
    """Простое хранилище в памяти (для разработки)"""
    
    def __init__(self):
        self._workflows: Dict[str, WorkflowChain] = {}
        self._documents: Dict[str, List[DocumentInfo]] = {}
        self._chats: Dict[str, ChatInfo] = {}
        
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
        """Загрузить данные из файлов"""
        try:
            # Загружаем workflows
            workflows_file = os.path.join(self.data_dir, "workflows.json")
            if os.path.exists(workflows_file):
                with open(workflows_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, workflow_data in data.items():
                        self._workflows[chat_id] = WorkflowChain(**workflow_data)
            
            # Загружаем documents
            documents_file = os.path.join(self.data_dir, "documents.json")
            if os.path.exists(documents_file):
                with open(documents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, docs_data in data.items():
                        self._documents[chat_id] = [DocumentInfo(**doc) for doc in docs_data]
            
            # Загружаем chats
            chats_file = os.path.join(self.data_dir, "chats.json")
            if os.path.exists(chats_file):
                with open(chats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, chat_data in data.items():
                        self._chats[chat_id] = ChatInfo(**chat_data)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def _save_data(self):
        """Сохранить данные в файлы"""
        try:
            # Сохраняем workflows
            workflows_file = os.path.join(self.data_dir, "workflows.json")
            with open(workflows_file, 'w', encoding='utf-8') as f:
                data = {k: v.model_dump(mode='json') for k, v in self._workflows.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Сохраняем documents
            documents_file = os.path.join(self.data_dir, "documents.json")
            with open(documents_file, 'w', encoding='utf-8') as f:
                data = {k: [doc.model_dump(mode='json') for doc in v] 
                       for k, v in self._documents.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Сохраняем chats
            chats_file = os.path.join(self.data_dir, "chats.json")
            with open(chats_file, 'w', encoding='utf-8') as f:
                data = {k: v.model_dump(mode='json') for k, v in self._chats.items()}
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Error saving data: {e}")
    
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
    
    def delete_chat(self, chat_id: str) -> bool:
        result = super().delete_chat(chat_id)
        if result:
            self._save_data()
        return result


# Singleton instance
_repository: Optional[InMemoryRepository] = None


def get_repository(use_file_storage: bool = True) -> InMemoryRepository:
    """Получить экземпляр repository"""
    global _repository
    if _repository is None:
        if use_file_storage:
            _repository = FileRepository()
        else:
            _repository = InMemoryRepository()
    return _repository
