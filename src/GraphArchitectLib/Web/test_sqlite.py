"""
Тесты для SQLite репозитория.

Проверяет:
- Создание и инициализацию БД
- Сохранение и загрузку агентов
- Работу с workflows, документами, чатами
- Сохранение истории выполнений
- Сохранение метрик обучения
"""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from database import Database
from sqlite_repository import SQLiteRepository
from models import Agent, WorkflowChain, WorkflowStep, DocumentInfo, ChatInfo


# ==================== Фикстуры ====================

@pytest.fixture
def temp_db():
    """Временная БД для тестов"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    
    yield db
    
    # Удаляем после теста
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def temp_repo(temp_db):
    """Временный репозиторий"""
    return SQLiteRepository(temp_db.db_path)


@pytest.fixture
def sample_agent():
    """Тестовый агент"""
    return Agent(
        id="test-agent",
        name="Test Agent",
        type="test",
        icon="🧪",
        color="#6366f1",
        specialization="Тестирование",
        capabilities=["testing"],
        cost=0.01,
        metrics={"avgScore": 0.85, "avgResponseTime": 1000}
    )


# ==================== Тесты Database ====================

class TestDatabase:
    """Тесты класса Database"""
    
    def test_database_creation(self, temp_db):
        """Создание БД"""
        assert Path(temp_db.db_path).exists()
    
    def test_tables_created(self, temp_db):
        """Таблицы созданы"""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = [row['name'] for row in cursor.fetchall()]
            
            expected_tables = [
                'agents', 'chats', 'documents', 'executions',
                'feedbacks', 'tool_metrics', 'workflows'
            ]
            
            for table in expected_tables:
                assert table in tables
    
    def test_insert_default_agents(self, temp_db):
        """Загрузка дефолтных агентов"""
        temp_db.insert_default_agents()
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            
            # Должно быть 24 агента из agent_library
            assert count == 24


# ==================== Тесты SQLiteRepository - Агенты ====================

class TestAgents:
    """Тесты работы с агентами"""
    
    def test_save_and_get_agent(self, temp_repo, sample_agent):
        """Сохранение и загрузка агента"""
        # Сохраняем
        temp_repo.save_agent(sample_agent)
        
        # Загружаем
        loaded = temp_repo.get_agent(sample_agent.id)
        
        assert loaded is not None
        assert loaded.id == sample_agent.id
        assert loaded.name == sample_agent.name
        assert loaded.type == sample_agent.type
        assert loaded.cost == sample_agent.cost
    
    def test_get_all_agents(self, temp_repo):
        """Получение всех агентов"""
        # Сохраняем несколько
        for i in range(5):
            agent = Agent(
                id=f"agent-{i}",
                name=f"Agent {i}",
                type="test",
                icon="🧪",
                color="#fff",
                cost=i * 0.01,
                metrics={}
            )
            temp_repo.save_agent(agent)
        
        # Загружаем всех
        agents = temp_repo.get_all_agents()
        
        assert len(agents) == 5
    
    def test_update_agent(self, temp_repo, sample_agent):
        """Обновление агента"""
        # Сохраняем
        temp_repo.save_agent(sample_agent)
        
        # Обновляем
        sample_agent.name = "Updated Name"
        sample_agent.cost = 0.05
        temp_repo.save_agent(sample_agent)
        
        # Проверяем
        loaded = temp_repo.get_agent(sample_agent.id)
        
        assert loaded.name == "Updated Name"
        assert loaded.cost == 0.05


# ==================== Тесты SQLiteRepository - Workflows ====================

class TestWorkflows:
    """Тесты работы с workflows"""
    
    def test_save_and_get_workflow(self, temp_repo):
        """Сохранение и загрузка workflow"""
        workflow = WorkflowChain(
            chat_id="test-chat",
            name="Test Workflow",
            steps=[],
            agents=[]
        )
        
        # Сохраняем
        temp_repo.save_workflow(workflow)
        
        # Загружаем
        loaded = temp_repo.get_workflow("test-chat")
        
        assert loaded is not None
        assert loaded.chat_id == "test-chat"
        assert loaded.name == "Test Workflow"
    
    def test_workflow_with_steps(self, temp_repo):
        """Workflow с шагами"""
        step = WorkflowStep(
            id="step-1",
            name="Test Step",
            order=1,
            candidateAgents=["agent-1", "agent-2"]
        )
        
        workflow = WorkflowChain(
            chat_id="test-chat",
            name="Test",
            steps=[step],
            agents=[]
        )
        
        temp_repo.save_workflow(workflow)
        loaded = temp_repo.get_workflow("test-chat")
        
        assert len(loaded.steps) == 1
        assert loaded.steps[0].name == "Test Step"


# ==================== Тесты SQLiteRepository - Документы ====================

class TestDocuments:
    """Тесты работы с документами"""
    
    def test_save_and_get_document(self, temp_repo):
        """Сохранение и загрузка документа"""
        doc = DocumentInfo(
            document_id="doc-1",
            chat_id="chat-1",
            filename="test.txt",
            content_type="text/plain",
            size=100,
            path="/uploads/test.txt"
        )
        
        temp_repo.save_document(doc)
        loaded = temp_repo.get_document("doc-1")
        
        assert loaded is not None
        assert loaded.document_id == "doc-1"
        assert loaded.filename == "test.txt"
    
    def test_get_documents_by_chat(self, temp_repo):
        """Получение документов чата"""
        # Создаем документы для разных чатов
        for i in range(3):
            doc = DocumentInfo(
                document_id=f"doc-{i}",
                chat_id="chat-1",
                filename=f"file{i}.txt",
                content_type="text/plain",
                size=100,
                path=f"/uploads/file{i}.txt"
            )
            temp_repo.save_document(doc)
        
        # Документ для другого чата
        doc = DocumentInfo(
            document_id="doc-other",
            chat_id="chat-2",
            filename="other.txt",
            content_type="text/plain",
            size=100,
            path="/uploads/other.txt"
        )
        temp_repo.save_document(doc)
        
        # Получаем документы chat-1
        docs = temp_repo.get_documents("chat-1")
        
        assert len(docs) == 3


# ==================== Тесты SQLiteRepository - Выполнения ====================

class TestExecutions:
    """Тесты истории выполнений"""
    
    def test_save_execution(self, temp_repo):
        """Сохранение истории выполнения"""
        temp_repo.save_execution(
            execution_id="exec-1",
            task_id="task-1",
            chat_id="chat-1",
            task_description="Тестовая задача",
            input_format="text|question",
            output_format="text|answer",
            algorithm_used="yen_5",
            status="COMPLETED",
            selected_tools=["Tool A", "Tool B"],
            gradient_traces=[{"temperature": 0.8}],
            result="Test result",
            total_time=2.5,
            total_cost=0.05
        )
        
        # Проверяем что сохранилось
        executions = temp_repo.get_executions()
        
        assert len(executions) == 1
        assert executions[0]['task_description'] == "Тестовая задача"
        assert executions[0]['status'] == "COMPLETED"
    
    def test_get_executions_statistics(self, temp_repo):
        """Статистика выполнений"""
        # Добавляем несколько выполнений
        for i in range(5):
            temp_repo.save_execution(
                execution_id=f"exec-{i}",
                task_id=f"task-{i}",
                chat_id="chat-1",
                task_description=f"Task {i}",
                input_format="text|question",
                output_format="text|answer",
                algorithm_used="dijkstra",
                status="COMPLETED" if i < 4 else "FAILED",
                selected_tools=["Tool A"],
                gradient_traces=[],
                result="Result",
                total_time=1.0,
                total_cost=0.01
            )
        
        stats = temp_repo.get_execution_statistics()
        
        assert stats['total_executions'] == 5
        assert stats['completed_executions'] == 4
        assert stats['success_rate'] == 0.8


# ==================== Тесты SQLiteRepository - Метрики ====================

class TestToolMetrics:
    """Тесты метрик инструментов"""
    
    def test_save_and_get_tool_metrics(self, temp_repo):
        """Сохранение и загрузка метрик"""
        temp_repo.save_tool_metrics(
            agent_id="agent-test",
            tool_name="Test Tool",
            reputation=0.87,
            mean_cost=0.02,
            mean_time=2.5,
            training_sample_size=50,
            variance_estimate=0.12,
            quality_scores=[0.8, 0.85, 0.9]
        )
        
        metrics = temp_repo.get_tool_metrics("agent-test")
        
        assert metrics is not None
        assert metrics['reputation'] == 0.87
        assert metrics['training_sample_size'] == 50
    
    def test_get_all_tool_metrics(self, temp_repo):
        """Получение метрик всех инструментов"""
        # Сохраняем метрики для нескольких инструментов
        for i in range(3):
            temp_repo.save_tool_metrics(
                agent_id=f"agent-{i}",
                tool_name=f"Tool {i}",
                reputation=0.5 + i * 0.1,
                mean_cost=0.01,
                mean_time=1.0,
                training_sample_size=10,
                variance_estimate=0.1,
                quality_scores=[]
            )
        
        all_metrics = temp_repo.get_all_tool_metrics()
        
        assert len(all_metrics) == 3
        # Должны быть отсортированы по reputation DESC
        assert all_metrics[0]['reputation'] >= all_metrics[1]['reputation']


# ==================== Интеграционные тесты ====================

class TestIntegration:
    """Интеграционные тесты"""
    
    def test_full_workflow_pipeline(self, temp_repo, sample_agent):
        """Полный пайплайн: агент → workflow → выполнение → метрики"""
        # 1. Сохраняем агента
        temp_repo.save_agent(sample_agent)
        
        # 2. Создаем чат
        chat = temp_repo.create_chat("test-chat", "Test Chat")
        assert chat is not None
        
        # 3. Сохраняем workflow
        workflow = WorkflowChain(
            chat_id="test-chat",
            name="Test Workflow",
            steps=[],
            agents=[sample_agent]
        )
        temp_repo.save_workflow(workflow)
        
        # 4. Сохраняем выполнение
        temp_repo.save_execution(
            execution_id="exec-1",
            task_id="task-1",
            chat_id="test-chat",
            task_description="Test",
            input_format="text|input",
            output_format="text|output",
            algorithm_used="dijkstra",
            status="COMPLETED",
            selected_tools=["Test Agent"],
            gradient_traces=[],
            result="Success",
            total_time=1.0,
            total_cost=0.01
        )
        
        # 5. Сохраняем feedback
        temp_repo.save_feedback(
            task_id="task-1",
            execution_id="exec-1",
            source="AUTO_CRITIC",
            quality_score=0.9,
            success=True
        )
        
        # 6. Сохраняем метрики
        temp_repo.save_tool_metrics(
            agent_id="test-agent",
            tool_name="Test Agent",
            reputation=0.87,
            mean_cost=0.01,
            mean_time=1.0,
            training_sample_size=1,
            variance_estimate=0.1,
            quality_scores=[0.9]
        )
        
        # Проверяем что всё сохранилось
        assert temp_repo.get_agent("test-agent") is not None
        assert temp_repo.get_chat("test-chat") is not None
        assert temp_repo.get_workflow("test-chat") is not None
        assert len(temp_repo.get_executions()) == 1
        assert len(temp_repo.get_feedbacks("task-1")) == 1
        assert temp_repo.get_tool_metrics("test-agent") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
