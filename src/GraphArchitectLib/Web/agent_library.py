"""
Библиотека агентов с их характеристиками и метриками
"""
from typing import List, Optional
from models import Agent

# Полная библиотека агентов
AGENT_LIBRARY = {
    # ===== Classifiers =====
    "agent-classifier-gpt4": Agent(
        id="agent-classifier-gpt4",
        name="GPT-4 Classifier",
        type="classification",
        icon="🤖",
        color="#10b981",
        specialization="Высокоточная классификация",
        capabilities=["advanced_nlp"],
        cost=0.03,
        metrics={
            "avgResponseTime": 2800,
            "avgScore": 0.98
        }
    ),
    "agent-classifier-claude": Agent(
        id="agent-classifier-claude",
        name="Claude Classifier",
        type="classification",
        icon="🧠",
        color="#6366f1",
        specialization="Глубокое понимание контекста",
        capabilities=["reasoning"],
        cost=0.02,
        metrics={
            "avgResponseTime": 3200,
            "avgScore": 0.95
        }
    ),
    "agent-classifier-local": Agent(
        id="agent-classifier-local",
        name="Local Classifier",
        type="classification",
        icon="💻",
        color="#8b5cf6",
        specialization="Быстрая локальная обработка",
        capabilities=["privacy"],
        cost=0.001,
        metrics={
            "avgResponseTime": 1200,
            "avgScore": 0.78
        }
    ),
    "agent-classifier-fast": Agent(
        id="agent-classifier-fast",
        name="Fast Classifier",
        type="classification",
        icon="⚡",
        color="#eab308",
        specialization="Сверхбыстрый анализ",
        capabilities=["speed"],
        cost=0.005,
        metrics={
            "avgResponseTime": 800,
            "avgScore": 0.72
        }
    ),
    
    # ===== Responders =====
    "agent-responder-creative": Agent(
        id="agent-responder-creative",
        name="Creative Responder",
        type="content_generation",
        icon="🎨",
        color="#ec4899",
        specialization="Творческие ответы",
        capabilities=["storytelling"],
        cost=0.025,
        metrics={
            "avgResponseTime": 4200,
            "avgScore": 0.85
        }
    ),
    "agent-responder-formal": Agent(
        id="agent-responder-formal",
        name="Formal Responder",
        type="content_generation",
        icon="📋",
        color="#3b82f6",
        specialization="Профессиональный тон",
        capabilities=["clarity"],
        cost=0.02,
        metrics={
            "avgResponseTime": 3800,
            "avgScore": 0.88
        }
    ),
    "agent-responder-technical": Agent(
        id="agent-responder-technical",
        name="Technical Responder",
        type="content_generation",
        icon="⚙️",
        color="#64748b",
        specialization="Детальные объяснения",
        capabilities=["documentation"],
        cost=0.035,
        metrics={
            "avgResponseTime": 5100,
            "avgScore": 0.86
        }
    ),
    "agent-responder-friendly": Agent(
        id="agent-responder-friendly",
        name="Friendly Responder",
        type="content_generation",
        icon="😊",
        color="#f59e0b",
        specialization="Эмпатичные ответы",
        capabilities=["empathy"],
        cost=0.015,
        metrics={
            "avgResponseTime": 3500,
            "avgScore": 0.92
        }
    ),
    
    # ===== QA Agents =====
    "agent-qa-strict": Agent(
        id="agent-qa-strict",
        name="Strict QA",
        type="quality_assurance",
        icon="🔍",
        color="#ef4444",
        specialization="Строгая проверка",
        capabilities=["thorough_review"],
        cost=0.01,
        metrics={
            "avgResponseTime": 2800,
            "avgScore": 0.99
        }
    ),
    "agent-qa-balanced": Agent(
        id="agent-qa-balanced",
        name="Balanced QA",
        type="quality_assurance",
        icon="⚖️",
        color="#10b981",
        specialization="Сбалансированный анализ",
        capabilities=["efficiency"],
        cost=0.008,
        metrics={
            "avgResponseTime": 2100,
            "avgScore": 0.87
        }
    ),
    "agent-qa-fast": Agent(
        id="agent-qa-fast",
        name="Fast QA",
        type="quality_assurance",
        icon="🚀",
        color="#eab308",
        specialization="Быстрый аудит",
        capabilities=["automated"],
        cost=0.005,
        metrics={
            "avgResponseTime": 1400,
            "avgScore": 0.76
        }
    ),
    
    # ===== Code Parsers =====
    "agent-parser-fast": Agent(
        id="agent-parser-fast",
        name="Fast Parser",
        type="code_analysis",
        icon="⚡",
        color="#eab308",
        specialization="Быстрый парсинг",
        capabilities=["syntax_check"],
        cost=0.005,
        metrics={
            "avgResponseTime": 1100,
            "avgScore": 0.80
        }
    ),
    "agent-parser-deep": Agent(
        id="agent-parser-deep",
        name="Deep Parser",
        type="code_analysis",
        icon="🔬",
        color="#8b5cf6",
        specialization="Глубокий анализ AST",
        capabilities=["dependencies"],
        cost=0.04,
        metrics={
            "avgResponseTime": 4500,
            "avgScore": 0.93
        }
    ),
    "agent-parser-incremental": Agent(
        id="agent-parser-incremental",
        name="Incremental Parser",
        type="code_analysis",
        icon="📊",
        color="#06b6d4",
        specialization="Инкрементальная обработка",
        capabilities=["caching"],
        cost=0.015,
        metrics={
            "avgResponseTime": 1800,
            "avgScore": 0.84
        }
    ),
    
    # ===== Code Analyzers =====
    "agent-security-scanner": Agent(
        id="agent-security-scanner",
        name="Security Scanner",
        type="code_analysis",
        icon="🛡️",
        color="#ef4444",
        specialization="Поиск уязвимостей",
        capabilities=["vulnerability_detection"],
        cost=0.05,
        metrics={
            "avgResponseTime": 5200,
            "avgScore": 0.90
        }
    ),
    "agent-performance-analyzer": Agent(
        id="agent-performance-analyzer",
        name="Performance Analyzer",
        type="code_analysis",
        icon="📈",
        color="#10b981",
        specialization="Анализ производительности",
        capabilities=["bottleneck_detection"],
        cost=0.045,
        metrics={
            "avgResponseTime": 4800,
            "avgScore": 0.87
        }
    ),
    "agent-style-checker": Agent(
        id="agent-style-checker",
        name="Style Checker",
        type="code_analysis",
        icon="✨",
        color="#ec4899",
        specialization="Проверка стиля",
        capabilities=["formatting"],
        cost=0.01,
        metrics={
            "avgResponseTime": 2200,
            "avgScore": 0.89
        }
    ),
    "agent-bug-detector": Agent(
        id="agent-bug-detector",
        name="Bug Detector",
        type="code_analysis",
        icon="🐛",
        color="#f59e0b",
        specialization="Обнаружение багов",
        capabilities=["pattern_matching"],
        cost=0.03,
        metrics={
            "avgResponseTime": 3900,
            "avgScore": 0.85
        }
    ),
    "agent-complexity-analyzer": Agent(
        id="agent-complexity-analyzer",
        name="Complexity Analyzer",
        type="code_analysis",
        icon="🧮",
        color="#6366f1",
        specialization="Анализ сложности",
        capabilities=["maintainability"],
        cost=0.02,
        metrics={
            "avgResponseTime": 3200,
            "avgScore": 0.88
        }
    ),
    
    # ===== Reporters =====
    "agent-reporter-detailed": Agent(
        id="agent-reporter-detailed",
        name="Detailed Reporter",
        type="reporting",
        icon="📄",
        color="#3b82f6",
        specialization="Детальные отчеты",
        capabilities=["analysis"],
        cost=0.025,
        metrics={
            "avgResponseTime": 3600,
            "avgScore": 0.88
        }
    ),
    "agent-reporter-summary": Agent(
        id="agent-reporter-summary",
        name="Summary Reporter",
        type="reporting",
        icon="📝",
        color="#10b981",
        specialization="Краткие сводки",
        capabilities=["key_points"],
        cost=0.01,
        metrics={
            "avgResponseTime": 2100,
            "avgScore": 0.84
        }
    ),
    "agent-reporter-interactive": Agent(
        id="agent-reporter-interactive",
        name="Interactive Reporter",
        type="reporting",
        icon="🎯",
        color="#ec4899",
        specialization="Интерактивные отчеты",
        capabilities=["drill_down"],
        cost=0.045,
        metrics={
            "avgResponseTime": 4200,
            "avgScore": 0.91
        }
    ),
    
    # ===== Content Creation Agents =====
    "agent-web-scraper": Agent(
        id="agent-web-scraper",
        name="Web Scraper",
        type="research",
        icon="🌐",
        color="#06b6d4",
        specialization="Сбор данных",
        capabilities=["extraction"],
        cost=0.015,
        metrics={
            "avgResponseTime": 4500,
            "avgScore": 0.83
        }
    ),
    "agent-academic-searcher": Agent(
        id="agent-academic-searcher",
        name="Academic Searcher",
        type="research",
        icon="🎓",
        color="#8b5cf6",
        specialization="Научные источники",
        capabilities=["credibility"],
        cost=0.06,
        metrics={
            "avgResponseTime": 5800,
            "avgScore": 0.92
        }
    ),
    "agent-trend-analyzer": Agent(
        id="agent-trend-analyzer",
        name="Trend Analyzer",
        type="research",
        icon="📊",
        color="#10b981",
        specialization="Анализ трендов",
        capabilities=["insights"],
        cost=0.03,
        metrics={
            "avgResponseTime": 3900,
            "avgScore": 0.86
        }
    ),
    "agent-outliner-structured": Agent(
        id="agent-outliner-structured",
        name="Structured Outliner",
        type="planning",
        icon="🗂️",
        color="#64748b",
        specialization="Структурные планы",
        capabilities=["logic"],
        cost=0.01,
        metrics={
            "avgResponseTime": 2800,
            "avgScore": 0.89
        }
    ),
    "agent-outliner-creative": Agent(
        id="agent-outliner-creative",
        name="Creative Outliner",
        type="planning",
        icon="💡",
        color="#f59e0b",
        specialization="Креативные структуры",
        capabilities=["perspectives"],
        cost=0.02,
        metrics={
            "avgResponseTime": 3300,
            "avgScore": 0.84
        }
    ),
    "agent-outliner-seo": Agent(
        id="agent-outliner-seo",
        name="SEO Outliner",
        type="planning",
        icon="🔍",
        color="#10b981",
        specialization="SEO-структуры",
        capabilities=["keywords"],
        cost=0.015,
        metrics={
            "avgResponseTime": 3100,
            "avgScore": 0.87
        }
    ),
    "agent-writer-formal": Agent(
        id="agent-writer-formal",
        name="Formal Writer",
        type="writing",
        icon="🖋️",
        color="#3b82f6",
        specialization="Формальный стиль",
        capabilities=["accuracy"],
        cost=0.03,
        metrics={
            "avgResponseTime": 6200,
            "avgScore": 0.88
        }
    ),
    "agent-writer-casual": Agent(
        id="agent-writer-casual",
        name="Casual Writer",
        type="writing",
        icon="✍️",
        color="#ec4899",
        specialization="Неформальный стиль",
        capabilities=["relatability"],
        cost=0.025,
        metrics={
            "avgResponseTime": 5100,
            "avgScore": 0.84
        }
    ),
    "agent-writer-technical": Agent(
        id="agent-writer-technical",
        name="Technical Writer",
        type="writing",
        icon="⚙️",
        color="#64748b",
        specialization="Техническая документация",
        capabilities=["precision"],
        cost=0.045,
        metrics={
            "avgResponseTime": 7200,
            "avgScore": 0.90
        }
    ),
    "agent-writer-storytelling": Agent(
        id="agent-writer-storytelling",
        name="Storytelling Writer",
        type="writing",
        icon="📖",
        color="#8b5cf6",
        specialization="Повествовательный стиль",
        capabilities=["narrative"],
        cost=0.035,
        metrics={
            "avgResponseTime": 6800,
            "avgScore": 0.87
        }
    ),
    "agent-grammar-checker": Agent(
        id="agent-grammar-checker",
        name="Grammar Checker",
        type="editing",
        icon="✅",
        color="#10b981",
        specialization="Проверка грамматики",
        capabilities=["spelling"],
        cost=0.005,
        metrics={
            "avgResponseTime": 2400,
            "avgScore": 0.92
        }
    ),
    "agent-style-improver": Agent(
        id="agent-style-improver",
        name="Style Improver",
        type="editing",
        icon="✨",
        color="#ec4899",
        specialization="Улучшение стиля",
        capabilities=["flow"],
        cost=0.015,
        metrics={
            "avgResponseTime": 3600,
            "avgScore": 0.87
        }
    ),
    "agent-fact-checker": Agent(
        id="agent-fact-checker",
        name="Fact Checker",
        type="editing",
        icon="🔍",
        color="#eab308",
        specialization="Проверка фактов",
        capabilities=["accuracy"],
        cost=0.04,
        metrics={
            "avgResponseTime": 4800,
            "avgScore": 0.90
        }
    ),
}


def get_agent(agent_id: str, use_db: bool = True) -> Optional[Agent]:
    """
    Получить агента по ID.
    
    Args:
        agent_id: ID агента
        use_db: Использовать БД (если доступна)
    
    Returns:
        Agent или None
    """
    # Пробуем загрузить из БД
    if use_db:
        try:
            from sqlite_repository import get_sqlite_repository
            repo = get_sqlite_repository()
            agent = repo.get_agent(agent_id)
            if agent:
                return agent
        except Exception as e:
            pass  # Fallback на хардкод
    
    # Fallback: хардкод из AGENT_LIBRARY
    return AGENT_LIBRARY.get(agent_id)


def get_agents_by_ids(agent_ids: List[str], use_db: bool = True) -> List[Agent]:
    """
    Получить список агентов по их ID.
    
    Args:
        agent_ids: Список ID агентов
        use_db: Использовать БД
    
    Returns:
        Список агентов
    """
    agents = []
    for aid in agent_ids:
        agent = get_agent(aid, use_db=use_db)
        if agent:
            agents.append(agent)
    return agents


def get_all_agents(use_db: bool = True) -> List[Agent]:
    """
    Получить всех агентов.
    
    Args:
        use_db: Использовать БД (если доступна)
    
    Returns:
        Список всех агентов
    
    Приоритет:
        1. Загрузить из SQLite БД (если доступна)
        2. Fallback на хардкод из AGENT_LIBRARY
    """
    # Пробуем загрузить из БД
    if use_db:
        try:
            from sqlite_repository import get_sqlite_repository
            repo = get_sqlite_repository()
            agents = repo.get_all_agents()
            
            if agents:
                print(f"  📦 Загружено агентов из БД: {len(agents)}")
                return agents
        except Exception as e:
            print(f"  ⚠️ БД не доступна ({e}), используется хардкод")
    
    # Fallback: хардкод из AGENT_LIBRARY
    print(f"  📦 Используются хардкод агенты: {len(AGENT_LIBRARY)}")
    return list(AGENT_LIBRARY.values())
