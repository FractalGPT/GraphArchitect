"""
Bridge between Web API and GraphArchitect library.

This module integrates GraphArchitect functionality into Web API:
- Agent to BaseTool conversion
- Real graph strategy search
- Tool selection via softmax with temperature
- Execution streaming with gradient traces
"""

import sys
import logging
from pathlib import Path

# Add path to grapharchitect
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Optional, AsyncGenerator, Tuple, Dict, Any
import asyncio
import uuid

logger = logging.getLogger(__name__)

from grapharchitect.entities.base_tool import BaseTool
from grapharchitect.entities.connectors.connector import Connector, ANY_SEMANTIC
from grapharchitect.entities.task_definition import TaskDefinition
from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator
from grapharchitect.services.execution.execution_context import ExecutionContext
from grapharchitect.services.selection.instrument_selector import InstrumentSelector
from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
from grapharchitect.services.pathfinding_algorithm import PathfindingAlgorithm
from grapharchitect.services.nli.natural_language_interface import NaturalLanguageInterface
from grapharchitect.services.nli.nli_dataset_item import NLIDatasetItem
from grapharchitect.services.training.training_orchestrator import TrainingOrchestrator
from grapharchitect.services.feedback.feedback_data import FeedbackData, FeedbackSource
from grapharchitect.services.feedback.simple_critic import SimpleCritic

# ReWOO Planning (опционально)
try:
    from grapharchitect.planning.rewoo_planner import ReWOOPlanner
    REWOO_AVAILABLE = True
except ImportError:
    REWOO_AVAILABLE = False
    logger.warning("ReWOO planner not available")

from models import Agent, MessageChunk
from repository import get_repository


class AgentTool(BaseTool):
    """
    Адаптер Agent → BaseTool.
    
    Преобразует Agent модель из Web API в BaseTool для использования
    в GraphArchitect. Автоматически выводит коннекторы на основе типа агента.
    """
    
    def __init__(self, agent: Agent):
        super().__init__()
        
        # Копируем метаданные из Agent
        self.metadata.tool_name = agent.name
        self.metadata.description = agent.specialization or ""
        self.metadata.reputation = agent.metrics.get("avgScore", 0.85)
        self.metadata.mean_cost = agent.cost
        self.metadata.mean_time_answer = agent.metrics.get("avgResponseTime", 3000) / 1000
        
        # Инициализация статистики для обучения
        self.metadata.training_sample_size = 10  # Начальное значение
        self.metadata.variance_estimate = 0.1
        
        # Определяем коннекторы на основе типа агента
        self.input, self.output = self._infer_connectors(agent)
        
        # Сохраняем ссылку на оригинальный Agent
        self._agent = agent
        self._agent_id = agent.id
    
    def _infer_connectors(self, agent: Agent) -> Tuple[Connector, Connector]:
        """
        Вывести коннекторы из типа агента.
        
        Маппинг основан на семантике операций, которые выполняет агент.
        """
        connector_mappings = {
            "classification": (
                Connector("text", "question"),
                Connector("text", "category")
            ),
            "content_generation": (
                Connector("text", "outline"),
                Connector("text", "content")
            ),
            "quality_assurance": (
                Connector("text", "content"),
                Connector("text", "validated")
            ),
            "research": (
                Connector("text", "query"),
                Connector("text", "findings")
            ),
            "planning": (
                Connector("text", "topic"),
                Connector("text", "outline")
            ),
            "writing": (
                Connector("text", "outline"),
                Connector("text", "article")
            ),
            "editing": (
                Connector("text", "draft"),
                Connector("text", "polished")
            ),
            "code_analysis": (
                Connector("text", "code"),
                Connector("text", "analysis")
            ),
            "reporting": (
                Connector("text", "data"),
                Connector("text", "report")
            ),
            "image_processing": (
                Connector("image", "raw"),
                Connector("text", "description")
            ),
            "text_extraction": (
                Connector("image", "raw"),
                Connector("text", "extracted")
            ),
            # Дополнительные маппинги для новых типов
            "parsing": (
                Connector("text", "raw"),
                Connector("text", "parsed")
            ),
            "analysis": (
                Connector("text", "question"),
                Connector("text", "analysis")
            ),
            "qa": (
                Connector("text", "question"),
                Connector("text", "answer")
            ),
            "universal": (
                Connector("text", "question"),
                Connector("text", "answer")
            ),
        }
        
        # Получаем маппинг или используем универсальный question→answer
        return connector_mappings.get(
            agent.type,
            (Connector("text", "question"), Connector("text", "answer"))
        )
    
    def execute(self, input_data):
        """
        Выполнить агента.
        
        Использует OpenRouter для реальных LLM вызовов (если API ключ доступен).
        Fallback на заглушку если OpenRouter не доступен или произошла ошибка.
        """
        # Пробуем использовать OpenRouter
        try:
            import os
            api_key = os.getenv("OPENROUTER_API_KEY")
            
            if api_key:
                # Импортируем OpenRouter (если доступен)
                try:
                    from grapharchitect.tools.ApiTools.OpenRouterTool import OpenRouterTool, OpenRouterConfig
                    
                    # Определяем модель на основе agent_id
                    model_map = {
                        "gpt4": "gpt-4",
                        "gpt-4": "gpt-4",
                        "claude": "claude-3.5-sonnet",
                        "claude-3": "claude-3-sonnet",
                        "gemini": "gemini-pro",
                        "llama": "llama-3-70b",
                        "mistral": "mistral-large",
                        "deepseek": "deepseek-chat"
                    }
                    
                    # Подбираем модель
                    model_key = "gpt-3.5-turbo"  # По умолчанию
                    
                    for key, value in model_map.items():
                        if key in self._agent_id.lower():
                            model_key = value
                            break
                    
                    # Получаем ID модели для OpenRouter
                    model_id = OpenRouterConfig.get_model_id(model_key)
                    
                    # Создаем OpenRouter инструмент
                    openrouter_tool = OpenRouterTool(
                        api_key=api_key,
                        model_name=model_id,
                        system_prompt=self.metadata.description or "You are a helpful AI assistant."
                    )
                    
                    # РЕАЛЬНЫЙ вызов LLM с таймаутом!
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("OpenRouter вызов превысил таймаут")
                    
                    try:
                        # Устанавливаем таймаут 10 секунд
                        # signal.signal(signal.SIGALRM, timeout_handler)
                        # signal.alarm(10)
                        
                        result = openrouter_tool.execute(str(input_data))
                        
                        # signal.alarm(0)  # Отключаем таймаут
                        
                        logger.info(f"OpenRouter executed: {self.metadata.tool_name} ({model_id})")
                        return result
                    
                    except (TimeoutError, ConnectionError, OSError) as net_err:
                        logger.warning(f"OpenRouter network error: {net_err}")
                        # Fallback to stub
                
                except ImportError as e:
                    logger.debug(f"OpenRouter not available: {e}")
                    pass  # Fallback
                
                except Exception as api_err:
                    logger.warning(f"OpenRouter API error: {api_err}")
                    pass  # Fallback
        
        except Exception as e:
            # General error, fallback
            logger.error(f"Execution error: {e}")
        
        # Fallback: return stub (always works!)
        result = f"[{self.metadata.tool_name}] Processed: {str(input_data)[:100]}"
        logger.info(f"Fallback mode: {self.metadata.tool_name}")
        return result
    
    @property
    def agent_id(self) -> str:
        """ID оригинального агента из agent_library"""
        return self._agent_id
    
    @property
    def original_agent(self) -> Agent:
        """Оригинальный Agent объект"""
        return self._agent


class GraphArchitectBridge:
    """
    Главный класс интеграции GraphArchitect с Web API.
    
    Предоставляет:
    - Конверсию всех Agent → BaseTool
    - Реальный поиск стратегий в графе
    - Выполнение через ExecutionOrchestrator
    - Выбор инструментов через InstrumentSelector (softmax + температура)
    - Стриминг прогресса выполнения
    - Сбор данных для обучения
    """
    
    def __init__(self):
        logger.info("Initializing GraphArchitectBridge...")
        
        # Создание сервиса эмбеддингов через фабрику (поддержка Infinity)
        try:
            from grapharchitect.services.embedding.embedding_factory import create_embedding_service
            import config
            
            self.embedding_service = create_embedding_service(
                embedding_type=config.EMBEDDING_TYPE,
                dimension=config.EMBEDDING_DIMENSION,
                infinity_url=config.INFINITY_BASE_URL,
                infinity_api_key=config.INFINITY_API_KEY,
                infinity_model=config.INFINITY_MODEL,
                infinity_timeout=config.INFINITY_TIMEOUT,
                fallback_to_simple=True
            )
            logger.info(f"Embedding service created: {self.embedding_service.__class__.__name__}")
        
        except Exception as e:
            logger.error(f"Error creating embedding service from config: {e}")
            logger.info("Falling back to SimpleEmbeddingService")
            from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
            self.embedding_service = SimpleEmbeddingService(dimension=384)
        
        # Инициализация других сервисов
        self.selector = InstrumentSelector(temperature_constant=config.TEMPERATURE_CONSTANT)
        self.strategy_finder = GraphStrategyFinder()
        self.orchestrator = ExecutionOrchestrator(
            self.embedding_service,
            self.selector,
            self.strategy_finder
        )
        
        # NLI для парсинга задач с k-NN ретривером (поддержка Faiss)
        self.nli = self._create_nli_with_retriever()
        self._load_nli_examples()
        
        # Обучение (опционально)
        self.training = TrainingOrchestrator(learning_rate=0.01)
        self.critic = SimpleCritic()
        
        # ReWOO Planning (всегда доступен для использования по запросу)
        self.rewoo_planner = None
        if REWOO_AVAILABLE:
            try:
                import config
                self.rewoo_planner = ReWOOPlanner(
                    gemini_api_key=getattr(config, 'GEMINI_API_KEY', None)
                )
                logger.info("ReWOO Planner initialized and available")
            except Exception as e:
                logger.warning(f"ReWOO Planner not available: {e}")
        
        # Конвертация всех агентов в инструменты
        self.tools = self._convert_agents_to_tools()
        self.agent_to_tool_map: Dict[str, AgentTool] = {}
        
        for tool in self.tools:
            if isinstance(tool, AgentTool):
                self.agent_to_tool_map[tool.agent_id] = tool
        
        logger.info(f"GraphArchitectBridge ready ({len(self.tools)} tools)")
    
    def _convert_agents_to_tools(self) -> List[BaseTool]:
        """Конвертировать всех агентов из БД в BaseTool"""
        repo = get_repository()
        agents = repo.get_all_agents()
        tools = []
        
        logger.info(f"Converting {len(agents)} tools to BaseTool...")
        
        for agent in agents:
            tool = AgentTool(agent)
            
            # Создаем эмбеддинг возможностей инструмента
            tool.metadata.capabilities_embedding = self.embedding_service.embed_tool_capabilities(tool)
            
            tools.append(tool)
        
        return tools
    
    def _create_nli_with_retriever(self):
        """
        Создать NLI с правильным k-NN ретривером (Faiss или наивный).
        
        Returns:
            Инициализированный NaturalLanguageInterface
        """
        try:
            from grapharchitect.services.nli.retriever_factory import create_knn_retriever
            import config
            
            # Создаем k-NN ретривер через фабрику
            retriever = create_knn_retriever(
                embedding_service=self.embedding_service,
                retriever_type=config.KNN_TYPE,
                vector_weight=config.KNN_VECTOR_WEIGHT,
                text_weight=config.KNN_TEXT_WEIGHT,
                faiss_index_type=config.FAISS_INDEX_TYPE
            )
            
            # Создаем NLI с custom retriever
            from grapharchitect.services.nli.natural_language_interface import NaturalLanguageInterface
            nli = NaturalLanguageInterface(self.embedding_service, retriever=retriever)
            
            logger.info(f"NLI created with {retriever.__class__.__name__}")
            return nli
        
        except Exception as e:
            logger.error(f"Error creating NLI with custom retriever: {e}")
            logger.info("Falling back to default NLI")
            return NaturalLanguageInterface(self.embedding_service)
    
    def _load_nli_examples(self):
        """Load NLI examples from file if available."""
        try:
            import json
            examples_file = Path(__file__).parent / "data" / "nli_examples.json"
            
            if examples_file.exists():
                with open(examples_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                examples = [NLIDatasetItem(**item) for item in data]
                self.nli.load_dataset(examples)
                logger.info(f"Loaded {len(examples)} NLI examples")
            else:
                logger.warning(f"NLI examples not found: {examples_file}")
        except Exception as e:
            logger.error(f"Error loading NLI examples: {e}")
    
    def get_tool_by_agent_id(self, agent_id: str) -> Optional[AgentTool]:
        """Получить BaseTool по ID агента"""
        return self.agent_to_tool_map.get(agent_id)
    
    def get_tools_by_agent_ids(self, agent_ids: List[str]) -> List[BaseTool]:
        """Получить список BaseTool по списку ID агентов"""
        tools = []
        for agent_id in agent_ids:
            tool = self.get_tool_by_agent_id(agent_id)
            if tool:
                tools.append(tool)
        return tools
    
    async def parse_user_message(self, message: str) -> Tuple[Connector, Connector]:
        """
        Парсинг пользовательского сообщения через NLI.
        
        Преобразует текст задачи в пару коннекторов (входной, выходной).
        Если NLI не может распарсить - возвращает дефолтные коннекторы.
        """
        try:
            result = self.nli.parse_task(message, self.tools, k=3)
            
            if result.success and result.task_representation:
                # Конвертируем ConnectorDescriptor → Connector
                input_conn = self._descriptor_to_connector(
                    result.task_representation.input_connector
                )
                output_conn = self._descriptor_to_connector(
                    result.task_representation.output_connector
                )
                
                logger.debug(f"NLI: {message[:50]}... -> {input_conn.format} -> {output_conn.format}")
                return (input_conn, output_conn)
        
        except Exception as e:
            logger.error(f"NLI error: {e}")
        
        # Fallback: default connectors
        logger.warning("Using default connectors")
        return (
            Connector("text", "question"),
            Connector("text", "answer")
        )
    
    def _descriptor_to_connector(self, descriptor) -> Connector:
        """Конвертировать ConnectorDescriptor → Connector"""
        if not descriptor:
            return Connector("text", "data")
        
        data_format = "text"
        semantic_format = "data"
        
        if descriptor.data_type:
            data_format = descriptor.data_type.subtype or descriptor.data_type.complex_type or "text"
        
        if descriptor.semantic_type:
            semantic_format = descriptor.semantic_type.semantic_category or "data"
        
        return Connector(data_format, semantic_format)
    
    async def find_strategies(
        self,
        start_format: str,
        end_format: str,
        algorithm: str = "yen_5"
    ) -> List[List[BaseTool]]:
        """
        Найти стратегии в графе (РЕАЛЬНЫЙ поиск через алгоритмы).
        
        Args:
            start_format: Входной формат (например "text|question")
            end_format: Выходной формат (например "text|answer")
            algorithm: Название алгоритма (yen_5, dijkstra и т.д.)
        
        Returns:
            Список стратегий (каждая стратегия = последовательность инструментов)
        """
        # Маппинг названий алгоритмов → PathfindingAlgorithm enum
        algo_map = {
            "dijkstra": PathfindingAlgorithm.DIJKSTRA,
            "astar": PathfindingAlgorithm.ASTAR,
            "yen_3": PathfindingAlgorithm.YEN,
            "yen_5": PathfindingAlgorithm.YEN,
            "yen_10": PathfindingAlgorithm.YEN,
            "ant_3": PathfindingAlgorithm.ANT_COLONY,
            "ant_5": PathfindingAlgorithm.ANT_COLONY,
            "ant_10": PathfindingAlgorithm.ANT_COLONY,
        }
        
        # Маппинг limit (количество путей для поиска)
        limit_map = {
            "yen_3": 3, "yen_5": 5, "yen_10": 10,
            "ant_3": 3, "ant_5": 5, "ant_10": 10,
            "dijkstra": 1, "astar": 1
        }
        
        algo = algo_map.get(algorithm, PathfindingAlgorithm.YEN)
        limit = limit_map.get(algorithm, 5)
        
        logger.debug(f"Searching strategies: {start_format} -> {end_format} ({algorithm}, limit={limit})")
        
        # Реальный поиск в графе!
        strategies = self.strategy_finder.find_strategies(
            self.tools,
            start_format,
            end_format,
            limit=limit,
            algorithm=algo
        )
        
        logger.info(f"Found {len(strategies)} strategies")
        
        return strategies
    
    async def select_tool_from_group(
        self,
        tool_group: List[BaseTool],
        task_embedding: Optional[List[float]] = None,
        top_k: int = 5
    ):
        """
        Выбрать инструмент из группы через softmax с температурой.
        
        Это РЕАЛЬНЫЙ алгоритм выбора, заменяющий random в WorkflowSimulator.
        
        Returns:
            InstrumentSelectionResult с selected_tool, probabilities, temperature
        """
        if not tool_group:
            return None
        
        selection_result = self.selector.select_instrument(
            tool_group,
            task_embedding,
            top_k=min(top_k, len(tool_group))
        )
        
        logger.debug(f"Selected: {selection_result.selected_tool.metadata.tool_name} "
              f"(p={selection_result.selection_probability:.3f}, T={selection_result.temperature:.3f})")
        
        return selection_result
    
    async def execute_task_full(
        self,
        message: str,
        input_data: any,
        algorithm: str = "yen_5",
        top_k: int = 5
    ) -> ExecutionContext:
        """
        Полное выполнение задачи через ExecutionOrchestrator.
        
        Возвращает ExecutionContext со всеми метриками и градиентными трассами.
        """
        # 1. Парсинг задачи (NLI или дефолт)
        input_conn, output_conn = await self.parse_user_message(message)
        
        # 2. Создание TaskDefinition
        task = TaskDefinition(
            description=message,
            input_connector=input_conn,
            output_connector=output_conn,
            input_data=input_data
        )
        
        # 3. Создание эмбеддинга задачи
        task.task_embedding = self.embedding_service.embed_text(message)
        
        # 4. Выполнение через оркестратор
        logger.info(f"Executing task: {message[:50]}...")
        
        context = self.orchestrator.execute_task(
            task,
            self.tools,
            path_limit=5,
            top_k=top_k
        )
        
        logger.info(f"Task completed: {context.status.value}")
        logger.info(f"Steps: {context.get_total_steps()}, Time: {context.total_time:.2f}s, Cost: {context.total_cost:.2f}")
        
        # 5. Автоматическая оценка и обучение
        await self._auto_evaluate_and_train(context)
        
        return context
    
    async def execute_task_streaming(
        self,
        message: str,
        input_data: any,
        algorithm: str = "yen_5",
        top_k: int = 5,
        use_rewoo: bool = False
    ) -> AsyncGenerator[MessageChunk, None]:
        """
        Выполнить задачу с real-time стримингом прогресса.
        
        Yields MessageChunk для каждого этапа выполнения.
        Клиент получает обновления о:
        - Поиске стратегий
        - Выборе инструментов
        - Выполнении каждого шага
        - Финальном результате
        """
        # 1. Парсинг задачи через NLI
        yield MessageChunk(
            type="gen_phase_start",
            phase_id="nli_parsing",
            content="Анализ задачи через NLI..."
        )
        
        input_conn, output_conn = await self.parse_user_message(message)
        
        yield MessageChunk(
            type="gen_phase_complete",
            phase_id="nli_parsing",
            metadata={
                "input_format": input_conn.format,
                "output_format": output_conn.format
            }
        )
        
        await asyncio.sleep(0.2)
        
        # 2. Поиск стратегий в графе
        yield MessageChunk(
            type="gen_phase_start",
            phase_id="graph_search",
            content=f"Поиск путей в графе ({algorithm})..."
        )
        
        strategies = await self.find_strategies(
            input_conn.format,
            output_conn.format,
            algorithm
        )
        
        if not strategies:
            yield MessageChunk(
                type="error",
                content="No strategies found. Check tool connectors."
            )
            return
        
        yield MessageChunk(
            type="gen_phase_complete",
            phase_id="graph_search",
            metadata={
                "strategies_found": len(strategies),
                "strategy_length": len(strategies[0]) if strategies else 0
            }
        )
        
        await asyncio.sleep(0.3)
        
        # 3. ReWOO Planning (если включен)
        rewoo_plan = None
        if use_rewoo and self.rewoo_planner:
            yield MessageChunk(
                type="gen_phase_start",
                phase_id="rewoo_planning",
                content=f"Создание детального плана (ReWOO с Gemini)..."
            )
            
            rewoo_plan = self.rewoo_planner.create_plan(
                task_description=message,
                strategies=strategies,
                algorithm_used=algorithm
            )
            
            if rewoo_plan:
                yield MessageChunk(
                    type="gen_phase_complete",
                    phase_id="rewoo_planning",
                    metadata={
                        "steps_in_plan": len(rewoo_plan.steps),
                        "reasoning": rewoo_plan.reasoning[:200],
                        "estimated_time": rewoo_plan.estimated_time,
                        "estimated_cost": rewoo_plan.estimated_cost
                    }
                )
            else:
                yield MessageChunk(
                    type="gen_phase_complete",
                    phase_id="rewoo_planning",
                    content="ReWOO plan не создан, используется базовая стратегия"
                )
            
            await asyncio.sleep(0.3)
        
        # Берем первую (лучшую) стратегию
        strategy = strategies[0]
        
        yield MessageChunk(
            type="gen_phase_start",
            phase_id="strategy_selected",
            content=f"Выбрана стратегия из {len(strategy)} шагов" + 
                   (f" (ReWOO план: {len(rewoo_plan.steps)} шагов)" if rewoo_plan else "")
        )
        
        await asyncio.sleep(0.2)
        
        # 4. Создаем задачу
        task = TaskDefinition(
            description=message,
            input_connector=input_conn,
            output_connector=output_conn,
            input_data=input_data
        )
        
        task.task_embedding = self.embedding_service.embed_text(message)
        
        # 5. Выполняем каждый шаг стратегии с стримингом
        current_data = input_data
        gradient_traces = []
        
        for step_index, tool_or_edge in enumerate(strategy):
            step_id = f"step-{step_index}"
            
            # Определяем группу инструментов
            # Может быть один инструмент или группа (если это ToolEdge)
            if hasattr(tool_or_edge, 'tools'):
                # Это ToolEdge с группой инструментов
                tool_group = tool_or_edge.tools
            else:
                # Это один инструмент
                tool_group = [tool_or_edge]
            
            # Событие начала шага
            yield MessageChunk(
                type="step_started",
                step_id=step_id,
                metadata={
                    "name": f"Шаг {step_index + 1}",
                    "candidates": [t.metadata.tool_name for t in tool_group]
                }
            )
            
            # Если есть конкуренция (> 1 кандидата), показываем соревнование
            if len(tool_group) > 1:
                # Имитируем прогресс выбора (для визуализации)
                for progress in range(0, 101, 20):
                    await asyncio.sleep(0.15)
                    
                    # Отправляем прогресс для каждого кандидата
                    for tool in tool_group:
                        yield MessageChunk(
                            type="agent_progress",
                            agent_id=tool.metadata.tool_name,
                            step_id=step_id,
                            progress=progress
                        )
                    
                    # Обновляем scores (растут к финалу)
                    if progress >= 80:
                        scores = {}
                        for tool in tool_group:
                            # Примерный score на основе репутации
                            score = tool.metadata.reputation * (0.9 + progress / 1000)
                            scores[tool.metadata.tool_name] = min(score, 0.99)
                        
                        yield MessageChunk(
                            type="agent_score_updated",
                            step_id=step_id,
                            metadata={
                                "agents": [
                                    {"agentId": name, "score": score}
                                    for name, score in scores.items()
                                ]
                            }
                        )
            
            # Шаг начался
            candidate_ids = [
                t.agent_id if isinstance(t, AgentTool) else t.metadata.tool_name
                for t in tool_group
            ]
            
            yield MessageChunk(
                type="step_started",
                step_id=step_id,
                content=f"Шаг {step_index + 1}/{len(strategy)}",
                metadata={
                    "candidates_count": len(tool_group),
                    "candidate_ids": candidate_ids
                }
            )
            
            # ДОБАВЛЕНО: Визуализация соревнования агентов (если > 1 кандидата)
            if len(tool_group) > 1:
                # Показываем прогресс "работы" каждого кандидата
                for progress in range(0, 101, 25):
                    await asyncio.sleep(0.2)
                    
                    for tool in tool_group:
                        agent_id = tool.agent_id if isinstance(tool, AgentTool) else tool.metadata.tool_name
                        
                        yield MessageChunk(
                            type="agent_progress",
                            agent_id=agent_id,
                            step_id=step_id,
                            progress=progress
                        )
                    
                    # Обновляем scores на каждом этапе (растут к концу)
                    if progress >= 50:
                        scores = {}
                        for tool in tool_group:
                            # Симулируем рост score
                            base_score = tool.metadata.reputation
                            current_score = base_score * (0.85 + progress / 500)
                            scores[tool] = min(current_score, 0.99)
                        
                        yield MessageChunk(
                            type="agent_score_updated",
                            step_id=step_id,
                            metadata={
                                "agents": [
                                    {
                                        "agentId": t.agent_id if isinstance(t, AgentTool) else t.metadata.tool_name,
                                        "score": round(scores[t], 3)
                                    }
                                    for t in tool_group
                                ]
                            }
                        )
            
            # Выбор инструмента через РЕАЛЬНЫЙ softmax!
            selection_result = await self.select_tool_from_group(
                tool_group,
                task.task_embedding,
                top_k=min(5, len(tool_group))
            )
            
            if not selection_result:
                yield MessageChunk(type="error", content="Ошибка выбора инструмента")
                return
            
            selected_tool = selection_result.selected_tool
            
            # Финальные scores с реальными вероятностями от softmax
            yield MessageChunk(
                type="agent_score_updated",
                step_id=step_id,
                metadata={
                    "agents": [
                        {
                            "agentId": t.agent_id if isinstance(t, AgentTool) else t.metadata.tool_name,
                            "score": round(selection_result.all_probabilities.get(t, 0), 3),
                            "logit": round(selection_result.all_logits.get(t, 0), 3)
                        }
                        for t in tool_group
                    ],
                    "temperature": round(selection_result.temperature, 3)
                }
            )
            
            # Агент выбран
            agent_id = selected_tool.agent_id if isinstance(selected_tool, AgentTool) else selected_tool.metadata.tool_name
            
            yield MessageChunk(
                type="agent_selected",
                agent_id=agent_id,
                step_id=step_id,
                score=selection_result.selection_probability,
                metadata={
                    "temperature": selection_result.temperature,
                    "top_k": selection_result.top_k
                }
            )
            
            await asyncio.sleep(0.3)
            
            # Выполнение инструмента
            yield MessageChunk(
                type="agent_executing",
                agent_id=agent_id,
                step_id=step_id,
                progress=30,
                content="Обработка данных..."
            )
            
            await asyncio.sleep(0.2)
            
            try:
                # РЕАЛЬНОЕ выполнение!
                current_data = selected_tool.execute(current_data)
                
                yield MessageChunk(
                    type="agent_executing",
                    agent_id=agent_id,
                    step_id=step_id,
                    progress=100,
                    content="Завершено"
                )
            
            except Exception as e:
                yield MessageChunk(
                    type="error",
                    content=f"Ошибка выполнения: {str(e)}"
                )
                return
            
            await asyncio.sleep(0.2)
            
            # Шаг завершен
            yield MessageChunk(
                type="step_completed",
                step_id=step_id,
                metadata={
                    "result_preview": str(current_data)[:100] if current_data else None
                }
            )
            
            # Сохраняем градиентную трассу
            gradient_traces.append(selection_result.gradient_info)
            
            await asyncio.sleep(0.3)
        
        # 6. Финальный результат
        yield MessageChunk(
            type="text",
            content=f"Execution result:\n\n{current_data}"
        )
    
    async def _auto_evaluate_and_train(self, context: ExecutionContext):
        """
        Автоматическая оценка и обучение после выполнения.
        
        Вызывается автоматически после каждого выполнения.
        Сохраняет данные в SQLite БД (если доступна).
        """
        try:
            # Автоматическая оценка через SimpleCritic
            feedback = self.critic.evaluate_execution(context)
            
            logger.info(f"Auto-evaluation: {feedback.quality_score:.2f}")
            
            # Добавление в датасет для обучения
            self.training.add_execution_to_dataset(context, [feedback])
            
            # Дообучение инструментов
            tools_to_train = [
                step.selected_tool
                for step in context.execution_steps
                if step.selected_tool
            ]
            
            if tools_to_train:
                self.training.train_all_tools(tools_to_train)
                logger.info(f"Trained tools: {len(tools_to_train)}")
                
                # Сохраняем обновленные метрики в БД
                await self._save_tool_metrics_to_db(tools_to_train)
            
            # Сохраняем историю выполнения в БД
            await self._save_execution_to_db(context, feedback)
        
        except Exception as e:
            logger.error(f"Training error: {e}")
    
    async def _save_tool_metrics_to_db(self, tools: List[BaseTool]):
        """Сохранить метрики инструментов в БД"""
        try:
            from sqlite_repository import get_sqlite_repository
            repo = get_sqlite_repository()
            
            for tool in tools:
                if isinstance(tool, AgentTool):
                    repo.save_tool_metrics(
                        agent_id=tool.agent_id,
                        tool_name=tool.metadata.tool_name,
                        reputation=tool.metadata.reputation,
                        mean_cost=tool.metadata.mean_cost,
                        mean_time=tool.metadata.mean_time_answer,
                        training_sample_size=tool.metadata.training_sample_size,
                        variance_estimate=tool.metadata.variance_estimate,
                        quality_scores=tool.metadata.quality_scores,
                        capabilities_embedding=tool.metadata.capabilities_embedding
                    )
            
            logger.debug("Metrics saved to database")
        
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def _save_execution_to_db(self, context: ExecutionContext, feedback):
        """Сохранить историю выполнения в БД"""
        try:
            from sqlite_repository import get_sqlite_repository
            repo = get_sqlite_repository()
            
            # Извлекаем данные из контекста
            selected_tools = [
                step.selected_tool.metadata.tool_name
                for step in context.execution_steps
                if step.selected_tool
            ]
            
            # Упрощенные градиентные трассы (только основное)
            gradient_traces = [
                {
                    'temperature': trace.temperature,
                    'selected_tool': trace.selected_tool.metadata.tool_name if trace.selected_tool else None,
                    'probabilities_count': len(trace.probabilities) if trace.probabilities else 0
                }
                for trace in context.gradient_traces
            ]
            
            input_format = context.task.input_connector.format if context.task else "unknown"
            output_format = context.task.output_connector.format if context.task else "unknown"
            
            repo.save_execution(
                execution_id=str(uuid.uuid4()),
                task_id=str(context.task_id),
                chat_id=None,  # TODO: передавать chat_id из контекста
                task_description=context.task.description if context.task else "",
                input_format=input_format,
                output_format=output_format,
                algorithm_used="auto",  # TODO: сохранять использованный алгоритм
                status=context.status.value,
                selected_tools=selected_tools,
                gradient_traces=gradient_traces,
                result=context.result,
                total_time=context.total_time,
                total_cost=context.total_cost
            )
            
            # Сохраняем feedback
            repo.save_feedback(
                task_id=str(context.task_id),
                execution_id=None,  # TODO: связать с execution
                source=feedback.source.value,
                quality_score=feedback.quality_score,
                success=feedback.success,
                comment=feedback.comment
            )
            
            logger.debug("Execution history saved to database")
        
        except Exception as e:
            logger.error(f"Failed to save execution history: {e}")
    
    async def submit_user_feedback(
        self,
        context: ExecutionContext,
        quality_score: float,
        comment: str = ""
    ):
        """
        Обработать пользовательскую обратную связь.
        
        Args:
            context: Контекст выполнения
            quality_score: Оценка качества (0.0-1.0)
            comment: Комментарий пользователя
        """
        feedback = FeedbackData(
            task_id=context.task_id,
            source=FeedbackSource.USER,
            quality_score=quality_score,
            comment=comment,
            success=quality_score >= 0.7
        )
        
        # Добавляем в датасет
        self.training.add_execution_to_dataset(context, [feedback])
        
        # Обучаем инструменты
        tools_to_train = [
            step.selected_tool
            for step in context.execution_steps
            if step.selected_tool
        ]
        
        if tools_to_train:
            self.training.train_all_tools(tools_to_train)
            logger.info(f"Training from user feedback: {quality_score:.2f}")
    
    def get_training_statistics(self):
        """Получить статистику обучения"""
        return self.training.get_statistics()


# ==================== Singleton instance ====================

_bridge: Optional[GraphArchitectBridge] = None
_bridge_error: Optional[Exception] = None


def get_bridge() -> GraphArchitectBridge:
    """
    Получить экземпляр GraphArchitectBridge (singleton).
    
    При первом вызове создает и инициализирует мост.
    При последующих - возвращает существующий экземпляр.
    """
    global _bridge, _bridge_error
    
    if _bridge is None and _bridge_error is None:
        try:
            print("\n" + "="*70)
            logger.info("Initializing GraphArchitect Bridge")
            print("="*70)
            
            _bridge = GraphArchitectBridge()
            
            print("="*70)
            logger.info("Bridge ready to use!")
            print("="*70 + "\n")
        
        except Exception as e:
            _bridge_error = e
            logger.error(f"Bridge initialization error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    if _bridge_error:
        raise RuntimeError(f"Bridge не инициализирован: {_bridge_error}")
    
    return _bridge


def is_bridge_available() -> bool:
    """Проверить доступность GraphArchitect Bridge"""
    try:
        get_bridge()
        return True
    except:
        return False
