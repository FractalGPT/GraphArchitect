"""
Симулятор выполнения workflow с конкурентным выбором агентов
"""
import asyncio
import random
from typing import Dict, Any, Optional, Callable
from models import WorkflowChain, WorkflowStep, CandidateProgress
from agent_library import get_agent

# ИНТЕГРАЦИЯ GraphArchitect
try:
    from grapharchitect_bridge import get_bridge, is_bridge_available, AgentTool
    GRAPHARCHITECT_ENABLED = True
except ImportError as e:
    GRAPHARCHITECT_ENABLED = False
    print(f"⚠️ WorkflowSimulator: GraphArchitect не доступен ({e})")


class WorkflowSimulator:
    """Симуляция выполнения workflow с real-time обновлениями через WebSocket"""
    
    def __init__(self, workflow: WorkflowChain, emit_callback: Callable):
        """
        Args:
            workflow: Workflow для выполнения
            emit_callback: Функция для отправки WebSocket сообщений
        """
        self.workflow = workflow
        self.emit = emit_callback
        self.is_running = False
        self.current_step_index = 0
    
    async def start(self):
        """Запустить выполнение workflow"""
        if self.is_running:
            return
        
        self.is_running = True
        print(f"🚀 Starting workflow: {self.workflow.name}")
        
        try:
            # Добавляем общий таймаут для всего workflow
            await asyncio.wait_for(
                self._run_workflow(),
                timeout=300  # 5 минут максимум
            )
        except asyncio.TimeoutError:
            print("⏱️ Workflow timeout reached")
            await self.emit("workflow_error", {
                "type": "workflow_error",
                "workflowId": self.workflow.chat_id,
                "error": "Workflow execution timeout"
            })
            self.is_running = False
        except Exception as e:
            print(f"❌ Error in workflow execution: {e}")
            import traceback
            traceback.print_exc()
            await self.emit("workflow_error", {
                "type": "workflow_error",
                "workflowId": self.workflow.chat_id,
                "error": str(e)
            })
            self.is_running = False
    
    async def _run_workflow(self):
        """Внутренний метод выполнения workflow"""
        try:
            # === ЭТАП 1: Генерация графа (3 фазы) ===
            await self.simulate_generation()
            
            if not self.is_running: return

            for step_index, step in enumerate(self.workflow.steps):
                if not self.is_running:
                    print(f"🛑 Workflow {self.workflow.chat_id} was stopped before step {step_index}")
                    break
                
                self.current_step_index = step_index
                print(f"\n📍 Step {step_index + 1}/{len(self.workflow.steps)}: {step.name}")
                
                # Начинаем шаг
                step.status = "in_progress"
                step.phase = "selection"
                
                await self.emit("step_started", {
                    "type": "step_started",
                    "workflowId": self.workflow.chat_id,
                    "stepId": step.id,
                    "stepIndex": step_index,
                    "stepName": step.name,
                    "candidateAgents": step.candidate_agents
                })
                
                # Запускаем конкурентный выбор агентов
                winner = await self.run_agent_selection(step)
                
                if not winner or not self.is_running:
                    print(f"⚠️ Selection failed, cancelled or stopped for step {step.name}")
                    break
                
                # Победитель выбран!
                step.selected_agent_id = winner["id"]
                step.phase = "executing"
                
                await self.emit("agent_selected", {
                    "type": "agent_selected",
                    "workflowId": self.workflow.chat_id,
                    "stepId": step.id,
                    "winnerId": winner["id"],
                    "score": winner["score"]
                })
                
                # Небольшая пауза перед "вторым проходом"
                await asyncio.sleep(1.0)
                
                if not self.is_running: break
                
                # Выполнение задачи победителем
                await self.execute_task(step, winner)
                
                if not self.is_running: break
                
                # Шаг завершен
                step.status = "completed"
                step.phase = "completed"
                
                next_step_id = None
                if step_index < len(self.workflow.steps) - 1:
                    next_step_id = self.workflow.steps[step_index + 1].id
                
                await self.emit("step_completed", {
                    "type": "step_completed",
                    "workflowId": self.workflow.chat_id,
                    "stepId": step.id,
                    "result": step.result,
                    "nextStepId": next_step_id
                })
                
                # Пауза между шагами
                for _ in range(10):
                    if not self.is_running: break
                    await asyncio.sleep(0.1)
            
            if self.is_running:
                # Workflow завершен
                self.is_running = False
                
                # Генерируем финальный ответ
                final_answer = f"Граф '{self.workflow.name}' успешно выполнен. " \
                              f"Все {len(self.workflow.steps)} этапов завершены. " \
                              f"Итоговый результат сформирован и проверен."

                await self.emit("workflow_completed", {
                    "type": "workflow_completed",
                    "workflowId": self.workflow.chat_id,
                    "finalAnswer": final_answer,
                    "results": [
                        {
                            "stepId": s.id,
                            "stepName": s.name,
                            "selectedAgent": s.selected_agent_id,
                            "status": s.status
                        }
                        for s in self.workflow.steps
                    ]
                })
                
                print(f"\n✅ Workflow completed: {self.workflow.name}")
        except Exception as e:
            print(f"❌ Error in _run_workflow: {e}")
            raise e

    async def simulate_generation(self):
        """Симуляция 3-этапной генерации графа с учетом алгоритма планирования"""
        # Определяем количество цепочек на основе алгоритма
        top_k = 1
        name_lower = self.workflow.name.lower()
        if "top-3" in name_lower: top_k = 3
        elif "top-5" in name_lower: top_k = 5
        elif "top-10" in name_lower: top_k = 10
        elif "yen" in name_lower or "ant" in name_lower:
            top_k = 5 # По умолчанию
            
        phases = [
            {"id": "knn", "name": "Поиск похожих архитектур в k-NN..."},
            {"id": "graph_algo", "name": f"Генерация {top_k} вариантов цепей ({self.workflow.name})"},
            {"id": "llm_refine", "name": f"LLM-синтез оптимального графа из Top-{top_k} путей"}
        ]
        
        print(f"  🏗️ Generating graph architecture using {self.workflow.name}...")
        
        for phase in phases:
            if not self.is_running: break
            
            await self.emit("generation_phase_started", {
                "type": "generation_phase_started",
                "workflowId": self.workflow.chat_id,
                "phaseId": phase["id"],
                "phaseName": phase["name"]
            })
            
            # Имитируем работу фазы
            steps = 5
            for i in range(steps):
                if not self.is_running: break
                progress = int(((i + 1) / steps) * 100)
                await self.emit("generation_progress", {
                    "type": "generation_progress",
                    "workflowId": self.workflow.chat_id,
                    "phaseId": phase["id"],
                    "progress": progress
                })
                await asyncio.sleep(0.4) # Общее время на фазу ~2 сек
            
            await self.emit("generation_phase_completed", {
                "type": "generation_phase_completed",
                "workflowId": self.workflow.chat_id,
                "phaseId": phase["id"]
            })
            await asyncio.sleep(0.2)

    async def run_agent_selection(self, step: WorkflowStep) -> Optional[Dict[str, Any]]:
        """Конкурентный выбор агентов (РЕАЛЬНЫЙ или симуляция)"""
        try:
            candidate_ids = step.candidate_agents
            strategy = step.selection_criteria.strategy
            timeout = step.selection_criteria.timeout / 1000  # конвертируем в секунды
            
            print(f"  🏁 Starting agent selection ({strategy}, timeout={timeout}s)")
            print(f"  👥 Candidates: {len(candidate_ids)} agents")
        except Exception as e:
            print(f"  ❌ Error in agent selection setup: {e}")
            return None
        
        # ПРОВЕРКА: Использовать GraphArchitect или симуляцию
        if GRAPHARCHITECT_ENABLED and is_bridge_available():
            # ✅ РЕАЛЬНЫЙ выбор через InstrumentSelector
            return await self._run_agent_selection_real(step, candidate_ids, strategy)
        else:
            # ⚠️ СИМУЛЯЦИЯ (fallback)
            return await self._run_agent_selection_simulation(step, candidate_ids, strategy, timeout)
    
    async def _run_agent_selection_real(
        self,
        step: WorkflowStep,
        candidate_ids: List[str],
        strategy: str
    ) -> Optional[Dict[str, Any]]:
        """РЕАЛЬНЫЙ выбор через GraphArchitect InstrumentSelector"""
        print(f"    🚀 Режим: GraphArchitect (реальный softmax)")
        
        try:
            bridge = get_bridge()
            
            # Получаем BaseTool для каждого кандидата
            tools = bridge.get_tools_by_agent_ids(candidate_ids)
            
            if not tools:
                print(f"    ❌ Инструменты не найдены для агентов: {candidate_ids}")
                return None
            
            # Адаптируем strategy → temperature_constant
            temp_map = {
                "fastest_response": 0.3,    # Низкая T → концентрация на лучших
                "best_quality_score": 1.0,  # Стандартная T
                "consensus": 0.7,           # Средняя T
                "balanced": 0.5             # Умеренная T
            }
            
            bridge.selector._temperature_constant = temp_map.get(strategy, 1.0)
            
            # РЕАЛЬНЫЙ выбор через softmax с температурой!
            selection_result = await bridge.select_tool_from_group(
                tools,
                task_embedding=None,  # TODO: получить из контекста задачи
                top_k=len(tools)
            )
            
            if not selection_result:
                return None
            
            # Отправляем РЕАЛЬНЫЕ метрики клиенту
            all_agents_data = []
            for tool, prob in selection_result.all_probabilities.items():
                if isinstance(tool, AgentTool):
                    logit = selection_result.all_logits.get(tool, 0)
                    
                    all_agents_data.append({
                        "agentId": tool.agent_id,
                        "score": round(prob, 3),
                        "logit": round(logit, 3)
                    })
                    
                    # Отправляем обновление score
                    await self.emit("agent_score_updated", {
                        "type": "agent_score_updated",
                        "workflowId": self.workflow.chat_id,
                        "stepId": step.id,
                        "agentId": tool.agent_id,
                        "score": round(prob, 3),
                        "logit": round(logit, 3),
                        "temperature": round(selection_result.temperature, 3)
                    })
            
            # Финальное обновление всех scores
            await self.emit("agent_score_updated", {
                "type": "agent_score_updated",
                "workflowId": self.workflow.chat_id,
                "stepId": step.id,
                "agents": all_agents_data,
                "temperature": round(selection_result.temperature, 3)
            })
            
            # Возвращаем победителя
            winner_tool = selection_result.selected_tool
            if isinstance(winner_tool, AgentTool):
                return {
                    "id": winner_tool.agent_id,
                    "score": selection_result.selection_probability
                }
            else:
                return {
                    "id": winner_tool.metadata.tool_name,
                    "score": selection_result.selection_probability
                }
        
        except Exception as e:
            print(f"    ❌ Ошибка в GraphArchitect выборе: {e}")
            import traceback
            traceback.print_exc()
            # Fallback на симуляцию
            return await self._run_agent_selection_simulation(step, candidate_ids, strategy, 10.0)
    
    async def _run_agent_selection_simulation(
        self,
        step: WorkflowStep,
        candidate_ids: List[str],
        strategy: str,
        timeout: float
    ) -> Optional[Dict[str, Any]]:
        """СИМУЛЯЦИЯ выбора (fallback режим)"""
        print(f"    ⚠️ Режим: Симуляция (random)")
        
        # Инициализация прогресса кандидатов
        candidates = []
        for agent_id in candidate_ids:
            agent = get_agent(agent_id)
            if agent:
                candidates.append({
                    "agentId": agent_id,
                    "agentData": agent,
                    "status": "competing",
                    "progress": 0,
                    "score": None,
                    "finalScore": 0
                })
        
        step.candidates_progress = [
            CandidateProgress(
                agent_id=c["agentId"],
                status="competing",
                progress=0,
                score=None
            )
            for c in candidates
        ]
        
        # Симуляция параллельной работы агентов
        start_time = asyncio.get_event_loop().time()
        update_interval = 0.15  # Обновление каждые 150ms
        
        leader_id = None
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed >= timeout or not self.is_running:
                print(f"  ⏱️ Selection timeout reached or stopped")
                break
            
            # Обновляем прогресс каждого агента
            for candidate in candidates:
                if candidate["progress"] < 100:
                    agent_data = candidate["agentData"]
                    # Ускоряем выбор в 3 раза (делим среднее время на 3)
                    avg_time = (agent_data.metrics.get("avgResponseTime", 3000) / 1000) / 3 
                    
                    # Симуляция прогресса на основе средней скорости агента
                    progress_rate = (update_interval / avg_time) * 100
                    random_factor = random.uniform(-3, 5)  # Добавляем случайность
                    candidate["progress"] = min(100, candidate["progress"] + progress_rate + random_factor)
                    
                    # Генерация score по мере прогресса
                    if candidate["progress"] > 25 and candidate["score"] is None:
                        base_score = agent_data.metrics.get("avgScore", 0.85)
                        random_variance = random.uniform(-0.08, 0.08)
                        candidate["score"] = max(0, min(1, base_score + random_variance))
                        
                        # Обновляем score
                        await self.emit("agent_score_updated", {
                            "type": "agent_score_updated",
                            "workflowId": self.workflow.chat_id,
                            "stepId": step.id,
                            "agentId": candidate["agentId"],
                            "score": round(candidate["score"], 3),
                            "agents": [
                                {
                                    "agentId": c["agentId"],
                                    "score": round(c["score"], 3) if c["score"] is not None else None,
                                    "progress": int(c["progress"])
                                }
                                for c in candidates
                            ]
                        })
                    
                    # Обновляем прогресс
                    await self.emit("agent_progress", {
                        "type": "agent_progress",
                        "workflowId": self.workflow.chat_id,
                        "stepId": step.id,
                        "agentId": candidate["agentId"],
                        "progress": int(candidate["progress"])
                    })
            
            # Определяем текущего лидера
            new_leader = self.get_current_leader(candidates, strategy)
            if new_leader and new_leader != leader_id:
                leader_id = new_leader
                print(f"  🏆 New leader: {leader_id}")
            
            # Проверка на завершение всех агентов
            all_completed = all(c["progress"] >= 100 for c in candidates)
            if all_completed:
                print(f"  ✅ All candidates completed")
                break
            
            await asyncio.sleep(update_interval)
        
        # Выбираем победителя по стратегии
        winner = self.select_winner(candidates, strategy)
        
        if winner:
            print(f"  🎯 Winner selected: {winner['id']} (score: {winner['score']:.3f})")
        
        return winner
    
    def get_current_leader(self, candidates, strategy) -> Optional[str]:
        """Определить текущего лидера"""
        valid_candidates = [c for c in candidates if c["score"] is not None]
        
        if not valid_candidates:
            return None
        
        if strategy == "fastest_response":
            leader = max(valid_candidates, key=lambda c: c["progress"])
        elif strategy == "best_quality_score":
            leader = max(valid_candidates, key=lambda c: c["score"])
        else:
            # Balanced approach
            leader = max(valid_candidates, key=lambda c: 
                        (c["score"] or 0) * 0.6 + (c["progress"] / 100) * 0.4)
        
        return leader["agentId"]
    
    def select_winner(self, candidates, strategy) -> Optional[Dict[str, Any]]:
        """Выбрать победителя по стратегии"""
        winner = None
        
        if strategy == "fastest_response":
            # Первый завершивший с максимальным прогрессом
            winner = max(candidates, key=lambda c: c["progress"])
            winner["finalScore"] = winner["score"] if winner["score"] else 0.85
            
        elif strategy == "best_quality_score":
            # Лучший score
            winner = max(candidates, key=lambda c: c["score"] if c["score"] else 0)
            winner["finalScore"] = winner["score"] if winner["score"] else 0.85
            
        elif strategy == "consensus":
            # Симуляция консенсуса - среднее между score и прогрессом
            for c in candidates:
                score = c["score"] if c["score"] else 0.5
                progress_factor = c["progress"] / 100
                c["finalScore"] = score * 0.7 + progress_factor * 0.3
            
            winner = max(candidates, key=lambda c: c["finalScore"])
            
        elif strategy == "balanced":
            # Баланс между качеством и скоростью
            for c in candidates:
                speed_factor = c["progress"] / 100
                quality_factor = c["score"] if c["score"] else 0.5
                c["finalScore"] = speed_factor * 0.4 + quality_factor * 0.6
            
            winner = max(candidates, key=lambda c: c["finalScore"])
        
        else:
            # По умолчанию - первый
            winner = candidates[0]
            winner["finalScore"] = winner["score"] if winner["score"] else 0.85
        
        return {
            "id": winner["agentId"],
            "score": winner["finalScore"]
        } if winner else None
    
    async def execute_task(self, step: WorkflowStep, winner: Dict[str, Any]):
        """Симуляция выполнения задачи победившим агентом"""
        agent = get_agent(winner["id"])
        if not agent:
            return
        
        execution_time = agent.metrics.get("avgResponseTime", 3000) / 1000  # в секунды
        steps_count = 10
        step_time = execution_time / steps_count
        
        actions = [
            "Инициализация задачи...",
            "Анализ входных данных...",
            "Обработка информации...",
            "Применение алгоритмов...",
            "Генерация результатов...",
            "Валидация выхода...",
            "Оптимизация решения...",
            "Проверка качества...",
            "Финализация результатов...",
            "Задача завершена"
        ]
        
        # Если есть файлы, добавляем специфическое действие
        if self.workflow.files:
            actions[1] = f"Анализ {len(self.workflow.files)} файл(ов)..."
            actions[2] = f"Извлечение данных из документов..."
        
        print(f"  ⚙️ Executing task with {agent.name}")
        
        for i in range(steps_count):
            if not self.is_running:
                break
            
            progress = int(((i + 1) / steps_count) * 100)
            
            await self.emit("agent_executing", {
                "type": "agent_executing",
                "workflowId": self.workflow.chat_id,
                "stepId": step.id,
                "agentId": winner["id"],
                "progress": progress,
                "action": actions[i]
            })
            
            await asyncio.sleep(step_time)
        
        step.result = {
            "success": True,
            "executionTime": execution_time,
            "agentName": agent.name
        }
        
        print(f"  ✅ Task completed by {agent.name}")
    
    async def stop(self):
        """Остановить выполнение"""
        print("🛑 Stopping workflow...")
        self.is_running = False
        
        # Отправляем событие об остановке
        try:
            await self.emit("workflow_stopped", {
                "type": "workflow_stopped",
                "workflowId": self.workflow.chat_id,
                "message": "Workflow остановлен пользователем"
            })
        except Exception as e:
            print(f"Error sending stop event: {e}")
        
        print("🛑 Workflow stopped")
