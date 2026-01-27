"""
Мост между Web API и библиотекой GraphArchitect.

Этот модуль интегрирует всю функциональность GraphArchitect в Web API:
- Конверсия Agent → BaseTool
- Реальный поиск стратегий в графе
- Выбор инструментов через softmax с температурой
- Стриминг выполнения с градиентными трассами
"""

import sys
from pathlib import Path

# Добавляем путь к grapharchitect
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Optional, AsyncGenerator, Tuple, Dict, Any
import asyncio

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

from models import Agent, MessageChunk
from agent_library import get_all_agents, get_agent


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
        }
        
        return connector_mappings.get(
            agent.type,
            (Connector("text", "input"), Connector("text", "output"))
        )
    
    def execute(self, input_data):
        """
        Выполнить агента.
        
        ⚠️ ЗАГЛУШКА: В продакшене заменить на реальный LLM API:
        - OpenAI для GPT-4 агентов
        - Anthropic для Claude агентов
        - Локальные модели для Local агентов
        """
        # TODO: Интеграция с реальными API
        # Примеры закомментированы ниже:
        
        # if "gpt4" in self._agent_id.lower():
        #     import openai
        #     response = openai.ChatCompletion.create(
        #         model="gpt-4",
        #         messages=[{"role": "user", "content": str(input_data)}]
        #     )
        #     return response.choices[0].message.content
        
        # elif "claude" in self._agent_id.lower():
        #     import anthropic
        #     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        #     message = client.messages.create(
        #         model="claude-3-opus-20240229",
        #         messages=[{"role": "user", "content": str(input_data)}]
        #     )
        #     return message.content[0].text
        
        # Fallback: возвращаем обработанные данные
        return f"[{self.metadata.tool_name}] Обработано: {input_data}"
    
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
        print("🔧 Инициализация GraphArchitectBridge...")
        
        # Инициализация сервисов GraphArchitect
        self.embedding_service = SimpleEmbeddingService(dimension=384)
        self.selector = InstrumentSelector(temperature_constant=1.0)
        self.strategy_finder = GraphStrategyFinder()
        self.orchestrator = ExecutionOrchestrator(
            self.embedding_service,
            self.selector,
            self.strategy_finder
        )
        
        # NLI для парсинга задач (опционально)
        self.nli = NaturalLanguageInterface(self.embedding_service)
        self._load_nli_examples()
        
        # Обучение (опционально)
        self.training = TrainingOrchestrator(learning_rate=0.01)
        self.critic = SimpleCritic()
        
        # Конвертация всех агентов в инструменты
        self.tools = self._convert_agents_to_tools()
        self.agent_to_tool_map: Dict[str, AgentTool] = {}
        
        for tool in self.tools:
            if isinstance(tool, AgentTool):
                self.agent_to_tool_map[tool.agent_id] = tool
        
        print(f"✅ GraphArchitectBridge готов ({len(self.tools)} инструментов)")
    
    def _convert_agents_to_tools(self) -> List[BaseTool]:
        """Конвертировать всех агентов из agent_library в BaseTool"""
        agents = get_all_agents()
        tools = []
        
        print(f"  📦 Конвертация {len(agents)} агентов в BaseTool...")
        
        for agent in agents:
            tool = AgentTool(agent)
            
            # Создаем эмбеддинг возможностей инструмента
            tool.metadata.capabilities_embedding = self.embedding_service.embed_tool_capabilities(tool)
            
            tools.append(tool)
        
        return tools
    
    def _load_nli_examples(self):
        """Загрузить примеры для NLI (если есть файл)"""
        try:
            import json
            examples_file = Path(__file__).parent / "data" / "nli_examples.json"
            
            if examples_file.exists():
                with open(examples_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                examples = [NLIDatasetItem(**item) for item in data]
                self.nli.load_dataset(examples)
                print(f"  📚 Загружено {len(examples)} примеров для NLI")
            else:
                print(f"  ⚠️ NLI примеры не найдены: {examples_file}")
        except Exception as e:
            print(f"  ⚠️ Ошибка загрузки NLI примеров: {e}")
    
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
                
                print(f"  🧠 NLI: {message[:50]}... → {input_conn.format} → {output_conn.format}")
                return (input_conn, output_conn)
        
        except Exception as e:
            print(f"  ⚠️ NLI ошибка: {e}")
        
        # Fallback: дефолтные коннекторы
        print(f"  ⚠️ Используются дефолтные коннекторы")
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
        
        print(f"  🔍 Поиск стратегий: {start_format} → {end_format} ({algorithm}, limit={limit})")
        
        # Реальный поиск в графе!
        strategies = self.strategy_finder.find_strategies(
            self.tools,
            start_format,
            end_format,
            limit=limit,
            algorithm=algo
        )
        
        print(f"  ✅ Найдено стратегий: {len(strategies)}")
        
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
        
        print(f"    🎯 Выбран: {selection_result.selected_tool.metadata.tool_name} "
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
        print(f"\n🚀 Выполнение задачи: {message[:50]}...")
        
        context = self.orchestrator.execute_task(
            task,
            self.tools,
            path_limit=5,
            top_k=top_k
        )
        
        print(f"✅ Задача выполнена: {context.status.value}")
        print(f"  Шагов: {context.get_total_steps()}")
        print(f"  Время: {context.total_time:.2f}s")
        print(f"  Стоимость: {context.total_cost:.2f}")
        
        # 5. Автоматическая оценка и обучение
        await self._auto_evaluate_and_train(context)
        
        return context
    
    async def execute_task_streaming(
        self,
        message: str,
        input_data: any,
        algorithm: str = "yen_5",
        top_k: int = 5
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
                content="❌ Стратегии не найдены. Проверьте коннекторы агентов."
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
        
        # 3. Берем первую (лучшую) стратегию
        strategy = strategies[0]
        
        yield MessageChunk(
            type="gen_phase_start",
            phase_id="strategy_selected",
            content=f"Выбрана стратегия из {len(strategy)} шагов"
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
            
            await asyncio.sleep(0.2)
            
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
            
            # Отправляем scores всех кандидатов
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
            content=f"✅ Результат выполнения:\n\n{current_data}"
        )
    
    async def _auto_evaluate_and_train(self, context: ExecutionContext):
        """
        Автоматическая оценка и обучение после выполнения.
        
        Вызывается автоматически после каждого выполнения.
        """
        try:
            # Автоматическая оценка через SimpleCritic
            feedback = self.critic.evaluate_execution(context)
            
            print(f"  📊 Автооценка: {feedback.quality_score:.2f}")
            
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
                print(f"  🎓 Обучено инструментов: {len(tools_to_train)}")
        
        except Exception as e:
            print(f"  ⚠️ Ошибка при обучении: {e}")
    
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
            print(f"  🎓 Обучение на основе пользовательской обратной связи: {quality_score:.2f}")
    
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
            print("🌉 Инициализация GraphArchitect Bridge")
            print("="*70)
            
            _bridge = GraphArchitectBridge()
            
            print("="*70)
            print("✅ Bridge готов к использованию!")
            print("="*70 + "\n")
        
        except Exception as e:
            _bridge_error = e
            print(f"\n❌ Ошибка инициализации Bridge: {e}")
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
