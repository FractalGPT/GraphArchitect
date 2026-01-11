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
        specialization="Высокоточная классификация с использованием GPT-4",
        capabilities=["advanced_nlp", "context_understanding", "multi_language"],
        metrics={
            "avgResponseTime": 2800,
            "successRate": 0.96,
            "avgScore": 0.92
        }
    ),
    "agent-classifier-claude": Agent(
        id="agent-classifier-claude",
        name="Claude Classifier",
        type="classification",
        icon="🧠",
        color="#6366f1",
        specialization="Глубокое понимание контекста с Claude",
        capabilities=["reasoning", "nuance_detection", "accuracy"],
        metrics={
            "avgResponseTime": 3200,
            "successRate": 0.94,
            "avgScore": 0.90
        }
    ),
    "agent-classifier-local": Agent(
        id="agent-classifier-local",
        name="Local Classifier",
        type="classification",
        icon="💻",
        color="#8b5cf6",
        specialization="Быстрая локальная классификация",
        capabilities=["fast_processing", "offline", "privacy"],
        metrics={
            "avgResponseTime": 1200,
            "successRate": 0.82,
            "avgScore": 0.78
        }
    ),
    "agent-classifier-fast": Agent(
        id="agent-classifier-fast",
        name="Fast Classifier",
        type="classification",
        icon="⚡",
        color="#eab308",
        specialization="Сверхбыстрая классификация",
        capabilities=["ultra_fast", "basic_nlp"],
        metrics={
            "avgResponseTime": 800,
            "successRate": 0.75,
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
        specialization="Творческие и оригинальные ответы",
        capabilities=["creative_writing", "storytelling", "engagement"],
        metrics={
            "avgResponseTime": 4200,
            "successRate": 0.87,
            "avgScore": 0.85
        }
    ),
    "agent-responder-formal": Agent(
        id="agent-responder-formal",
        name="Formal Responder",
        type="content_generation",
        icon="📋",
        color="#3b82f6",
        specialization="Формальные и профессиональные ответы",
        capabilities=["professional_tone", "accuracy", "clarity"],
        metrics={
            "avgResponseTime": 3800,
            "successRate": 0.91,
            "avgScore": 0.88
        }
    ),
    "agent-responder-technical": Agent(
        id="agent-responder-technical",
        name="Technical Responder",
        type="content_generation",
        icon="⚙️",
        color="#64748b",
        specialization="Технические и детальные объяснения",
        capabilities=["technical_writing", "precision", "documentation"],
        metrics={
            "avgResponseTime": 5100,
            "successRate": 0.89,
            "avgScore": 0.86
        }
    ),
    "agent-responder-friendly": Agent(
        id="agent-responder-friendly",
        name="Friendly Responder",
        type="content_generation",
        icon="😊",
        color="#f59e0b",
        specialization="Дружелюбные и эмпатичные ответы",
        capabilities=["empathy", "warmth", "customer_satisfaction"],
        metrics={
            "avgResponseTime": 3500,
            "successRate": 0.93,
            "avgScore": 0.91
        }
    ),
    
    # ===== QA Agents =====
    "agent-qa-strict": Agent(
        id="agent-qa-strict",
        name="Strict QA",
        type="quality_assurance",
        icon="🔍",
        color="#ef4444",
        specialization="Строгая проверка качества",
        capabilities=["thorough_review", "high_standards", "detail_oriented"],
        metrics={
            "avgResponseTime": 2800,
            "successRate": 0.88,
            "avgScore": 0.84
        }
    ),
    "agent-qa-balanced": Agent(
        id="agent-qa-balanced",
        name="Balanced QA",
        type="quality_assurance",
        icon="⚖️",
        color="#10b981",
        specialization="Сбалансированная проверка",
        capabilities=["balanced_approach", "practical", "efficient"],
        metrics={
            "avgResponseTime": 2100,
            "successRate": 0.90,
            "avgScore": 0.87
        }
    ),
    "agent-qa-fast": Agent(
        id="agent-qa-fast",
        name="Fast QA",
        type="quality_assurance",
        icon="🚀",
        color="#eab308",
        specialization="Быстрая проверка",
        capabilities=["speed", "basic_checks", "automated"],
        metrics={
            "avgResponseTime": 1400,
            "successRate": 0.79,
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
        specialization="Быстрый парсинг кода",
        capabilities=["fast_parsing", "basic_ast", "syntax_check"],
        metrics={
            "avgResponseTime": 1100,
            "successRate": 0.85,
            "avgScore": 0.80
        }
    ),
    "agent-parser-deep": Agent(
        id="agent-parser-deep",
        name="Deep Parser",
        type="code_analysis",
        icon="🔬",
        color="#8b5cf6",
        specialization="Глубокий анализ структуры",
        capabilities=["deep_analysis", "full_ast", "dependencies"],
        metrics={
            "avgResponseTime": 4500,
            "successRate": 0.95,
            "avgScore": 0.93
        }
    ),
    "agent-parser-incremental": Agent(
        id="agent-parser-incremental",
        name="Incremental Parser",
        type="code_analysis",
        icon="📊",
        color="#06b6d4",
        specialization="Инкрементальный парсинг",
        capabilities=["incremental", "caching", "efficient"],
        metrics={
            "avgResponseTime": 1800,
            "successRate": 0.88,
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
        specialization="Поиск уязвимостей безопасности",
        capabilities=["vulnerability_detection", "security_best_practices"],
        metrics={
            "avgResponseTime": 5200,
            "successRate": 0.92,
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
        capabilities=["performance_optimization", "bottleneck_detection"],
        metrics={
            "avgResponseTime": 4800,
            "successRate": 0.89,
            "avgScore": 0.87
        }
    ),
    "agent-style-checker": Agent(
        id="agent-style-checker",
        name="Style Checker",
        type="code_analysis",
        icon="✨",
        color="#ec4899",
        specialization="Проверка стиля кода",
        capabilities=["style_enforcement", "code_formatting", "conventions"],
        metrics={
            "avgResponseTime": 2200,
            "successRate": 0.94,
            "avgScore": 0.89
        }
    ),
    "agent-bug-detector": Agent(
        id="agent-bug-detector",
        name="Bug Detector",
        type="code_analysis",
        icon="🐛",
        color="#f59e0b",
        specialization="Обнаружение потенциальных багов",
        capabilities=["bug_detection", "static_analysis", "pattern_matching"],
        metrics={
            "avgResponseTime": 3900,
            "successRate": 0.88,
            "avgScore": 0.85
        }
    ),
    "agent-complexity-analyzer": Agent(
        id="agent-complexity-analyzer",
        name="Complexity Analyzer",
        type="code_analysis",
        icon="🧮",
        color="#6366f1",
        specialization="Анализ сложности кода",
        capabilities=["complexity_metrics", "maintainability_index"],
        metrics={
            "avgResponseTime": 3200,
            "successRate": 0.91,
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
        capabilities=["comprehensive_reports", "detailed_analysis"],
        metrics={
            "avgResponseTime": 3600,
            "successRate": 0.90,
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
        capabilities=["concise_summaries", "key_points"],
        metrics={
            "avgResponseTime": 2100,
            "successRate": 0.87,
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
        capabilities=["interactive_visualizations", "drill_down"],
        metrics={
            "avgResponseTime": 4200,
            "successRate": 0.92,
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
        specialization="Сбор информации из интернета",
        capabilities=["web_scraping", "data_extraction", "real_time_info"],
        metrics={
            "avgResponseTime": 4500,
            "successRate": 0.86,
            "avgScore": 0.83
        }
    ),
    "agent-academic-searcher": Agent(
        id="agent-academic-searcher",
        name="Academic Searcher",
        type="research",
        icon="🎓",
        color="#8b5cf6",
        specialization="Поиск научных источников",
        capabilities=["academic_search", "citation_management", "credibility"],
        metrics={
            "avgResponseTime": 5800,
            "successRate": 0.93,
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
        capabilities=["trend_analysis", "social_listening", "insights"],
        metrics={
            "avgResponseTime": 3900,
            "successRate": 0.88,
            "avgScore": 0.86
        }
    ),
    "agent-outliner-structured": Agent(
        id="agent-outliner-structured",
        name="Structured Outliner",
        type="planning",
        icon="🗂️",
        color="#64748b",
        specialization="Структурированные планы",
        capabilities=["logical_structure", "hierarchical_organization"],
        metrics={
            "avgResponseTime": 2800,
            "successRate": 0.91,
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
        capabilities=["creative_organization", "unique_perspectives"],
        metrics={
            "avgResponseTime": 3300,
            "successRate": 0.85,
            "avgScore": 0.84
        }
    ),
    "agent-outliner-seo": Agent(
        id="agent-outliner-seo",
        name="SEO Outliner",
        type="planning",
        icon="🔍",
        color="#10b981",
        specialization="SEO-оптимизированные структуры",
        capabilities=["seo_optimization", "keyword_placement", "search_intent"],
        metrics={
            "avgResponseTime": 3100,
            "successRate": 0.89,
            "avgScore": 0.87
        }
    ),
    "agent-writer-formal": Agent(
        id="agent-writer-formal",
        name="Formal Writer",
        type="writing",
        icon="🖋️",
        color="#3b82f6",
        specialization="Формальный стиль письма",
        capabilities=["formal_writing", "professional_tone", "accuracy"],
        metrics={
            "avgResponseTime": 6200,
            "successRate": 0.90,
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
        capabilities=["conversational_tone", "relatability", "engagement"],
        metrics={
            "avgResponseTime": 5100,
            "successRate": 0.86,
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
        capabilities=["technical_writing", "precision", "clarity"],
        metrics={
            "avgResponseTime": 7200,
            "successRate": 0.92,
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
        capabilities=["storytelling", "emotional_connection", "narrative"],
        metrics={
            "avgResponseTime": 6800,
            "successRate": 0.88,
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
        capabilities=["grammar_check", "spelling", "punctuation"],
        metrics={
            "avgResponseTime": 2400,
            "successRate": 0.95,
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
        capabilities=["style_enhancement", "readability", "flow"],
        metrics={
            "avgResponseTime": 3600,
            "successRate": 0.89,
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
        capabilities=["fact_verification", "source_validation", "accuracy"],
        metrics={
            "avgResponseTime": 4800,
            "successRate": 0.91,
            "avgScore": 0.90
        }
    ),
}


def get_agent(agent_id: str) -> Optional[Agent]:
    """Получить агента по ID"""
    return AGENT_LIBRARY.get(agent_id)


def get_agents_by_ids(agent_ids: List[str]) -> List[Agent]:
    """Получить список агентов по их ID"""
    return [AGENT_LIBRARY[aid] for aid in agent_ids if aid in AGENT_LIBRARY]


def get_all_agents() -> List[Agent]:
    """Получить всех агентов"""
    return list(AGENT_LIBRARY.values())
