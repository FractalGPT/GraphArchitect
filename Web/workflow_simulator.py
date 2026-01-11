"""
Симулятор выполнения workflow с конкурентным выбором агентов
"""
import asyncio
import random
from typing import Dict, Any, Optional, Callable
from models import WorkflowChain, WorkflowStep, CandidateProgress
from agent_library import get_agent


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

    async def run_agent_selection(self, step: WorkflowStep) -> Optional[Dict[str, Any]]:
        """Симуляция конкурентного выбора агентов"""
        try:
            candidate_ids = step.candidate_agents
            strategy = step.selection_criteria.strategy
            timeout = step.selection_criteria.timeout / 1000  # конвертируем в секунды
            
            print(f"  🏁 Starting agent selection ({strategy}, timeout={timeout}s)")
            print(f"  👥 Candidates: {len(candidate_ids)} agents")
        except Exception as e:
            print(f"  ❌ Error in agent selection setup: {e}")
            return None
        
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
                    avg_time = agent_data.metrics.get("avgResponseTime", 3000) / 1000  # в секунды
                    
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
