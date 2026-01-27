"""
SQLite3 база данных для GraphArchitect Web API.

Таблицы:
- agents - библиотека агентов (вместо хардкода)
- workflows - цепочки выполнения
- chats - информация о чатах
- documents - загруженные документы
- executions - история выполнений
- feedbacks - обратная связь для обучения
- tool_metrics - метрики инструментов
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str = "grapharchitect.db"):
        """
        Инициализация БД.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с соединением"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Создать таблицы если их нет"""
        print(f"📦 Инициализация SQLite БД: {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица агентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    icon TEXT,
                    color TEXT,
                    specialization TEXT,
                    capabilities TEXT,  -- JSON array
                    cost REAL DEFAULT 0.0,
                    metrics TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица workflows
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    chat_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    request_type TEXT,
                    steps TEXT,  -- JSON array
                    agents TEXT,  -- JSON array (для обратной совместимости)
                    files TEXT,  -- JSON array
                    current_step_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица чатов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица документов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT,
                    size INTEGER,
                    path TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
                )
            """)
            
            # Таблица истории выполнений (для обучения)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    chat_id TEXT,
                    task_description TEXT,
                    input_format TEXT,
                    output_format TEXT,
                    algorithm_used TEXT,
                    status TEXT,  -- COMPLETED, FAILED
                    selected_tools TEXT,  -- JSON array
                    gradient_traces TEXT,  -- JSON array
                    result TEXT,
                    total_time REAL,
                    total_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE SET NULL
                )
            """)
            
            # Таблица обратной связи
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedbacks (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    execution_id TEXT,
                    source TEXT,  -- USER, AUTO_CRITIC, SYSTEM
                    quality_score REAL NOT NULL,
                    success INTEGER,  -- 0 or 1
                    comment TEXT,
                    detailed_scores TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_id) REFERENCES executions(execution_id) ON DELETE CASCADE
                )
            """)
            
            # Таблица метрик инструментов (агрегированные данные)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_metrics (
                    agent_id TEXT PRIMARY KEY,
                    tool_name TEXT,
                    reputation REAL DEFAULT 0.5,
                    mean_cost REAL DEFAULT 1.0,
                    mean_time REAL DEFAULT 1.0,
                    training_sample_size INTEGER DEFAULT 1,
                    variance_estimate REAL DEFAULT 1.0,
                    quality_scores TEXT,  -- JSON array
                    capabilities_embedding TEXT,  -- JSON array
                    last_training_date TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                )
            """)
            
            # Индексы для ускорения запросов
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_chat_id 
                ON documents(chat_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_chat_id 
                ON executions(chat_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_created_at 
                ON executions(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedbacks_task_id 
                ON feedbacks(task_id)
            """)
            
            conn.commit()
            
            print("✅ Таблицы БД созданы/проверены")
    
    def insert_default_agents(self):
        """
        Вставить дефолтных агентов из agent_library.py в БД.
        
        Вызывается один раз при первом запуске.
        """
        from agent_library import AGENT_LIBRARY
        
        print("📥 Загрузка агентов в БД...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем сколько агентов уже в БД
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"  ℹ️ В БД уже есть {count} агентов, пропускаем загрузку")
                return
            
            # Вставляем всех агентов
            inserted = 0
            for agent_id, agent in AGENT_LIBRARY.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO agents 
                    (id, name, type, icon, color, specialization, capabilities, cost, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent.id,
                    agent.name,
                    agent.type,
                    agent.icon,
                    agent.color,
                    agent.specialization,
                    json.dumps(agent.capabilities),
                    agent.cost,
                    json.dumps(agent.metrics)
                ))
                inserted += 1
            
            conn.commit()
            print(f"✅ Загружено агентов в БД: {inserted}")
    
    def clear_all_data(self):
        """Очистить все таблицы (для тестирования)"""
        print("⚠️ Очистка всех данных...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            tables = [
                "feedbacks",
                "executions", 
                "tool_metrics",
                "documents",
                "workflows",
                "chats",
                "agents"
            ]
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            
            conn.commit()
            
            print("✅ Все данные очищены")


# Singleton instance
_database: Optional[Database] = None


def get_database(db_path: str = "grapharchitect.db") -> Database:
    """
    Получить экземпляр базы данных (singleton).
    
    Args:
        db_path: Путь к файлу БД
    
    Returns:
        Database instance
    """
    global _database
    
    if _database is None:
        _database = Database(db_path)
        
        # При первом запуске загружаем агентов из agent_library
        _database.insert_default_agents()
    
    return _database
