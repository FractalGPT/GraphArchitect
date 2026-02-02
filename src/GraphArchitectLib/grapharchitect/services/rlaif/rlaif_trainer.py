"""
RLAIF Trainer - обучение с обратной связью от AI.

Использует LLM критика для автоматической оценки качества
и обучения инструментов через Policy Gradient.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ..execution.execution_context import ExecutionContext
from ..feedback.feedback_data import FeedbackData, FeedbackSource
from ..training.training_orchestrator import TrainingOrchestrator
from .llm_critic import LLMCritic, LLMCriticScore
from ...entities.base_tool import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class RLAIFTrainingResult:
    """Результат RLAIF обучения."""
    
    evaluations_count: int
    average_score: float
    tools_updated: int
    improvements: Dict[str, float]  # tool_name → delta_reputation


class RLAIFTrainer:
    """
    Тренер с использованием RLAIF.
    
    Автоматически:
    1. Оценивает результаты через LLM критика
    2. Создает FeedbackData
    3. Обучает инструменты через TrainingOrchestrator
    """
    
    def __init__(
        self,
        llm_critic: LLMCritic,
        training_orchestrator: TrainingOrchestrator,
        min_score_threshold: float = 0.3,
        save_evaluations: bool = True
    ):
        """
        Инициализация RLAIF тренера.
        
        Args:
            llm_critic: LLM критик для оценки
            training_orchestrator: Оркестратор обучения
            min_score_threshold: Минимальный порог для обучения
            save_evaluations: Сохранять историю оценок
        """
        self._critic = llm_critic
        self._training = training_orchestrator
        self._min_threshold = min_score_threshold
        self._save_evaluations = save_evaluations
        
        # История оценок
        self._evaluation_history: List[LLMCriticScore] = []
        
        logger.info("RLAIF Trainer initialized")
    
    def evaluate_and_train(
        self,
        context: ExecutionContext,
        task_description: str,
        result: str
    ) -> RLAIFTrainingResult:
        """
        Оценить результат и обучить инструменты.
        
        Args:
            context: Контекст выполнения задачи
            task_description: Описание задачи
            result: Результат выполнения
            
        Returns:
            Результат обучения
        """
        # Шаг 1: Оценка через LLM критика
        critic_context = {
            'execution_time': context.total_time,
            'tools_used': [
                step.selected_tool.metadata.tool_name 
                for step in context.execution_steps
            ],
            'cost': context.total_cost
        }
        
        score = self._critic.evaluate_answer(
            task=task_description,
            answer=result,
            context=critic_context
        )
        
        logger.info(
            f"LLM Critic score: {score.overall_score:.2f} "
            f"(correct={score.correctness:.2f}, complete={score.completeness:.2f})"
        )
        
        # Сохранение оценки
        if self._save_evaluations:
            self._evaluation_history.append(score)
        
        # Шаг 2: Создание FeedbackData
        feedback = FeedbackData(
            task_id=context.task_id,
            source=FeedbackSource.AI_CRITIC,
            quality_score=score.overall_score,
            comment=score.reasoning,
            detailed_scores={
                'correctness': score.correctness,
                'completeness': score.completeness,
                'relevance': score.relevance,
                'clarity': score.clarity
            },
            success=score.overall_score >= self._min_threshold
        )
        
        # Шаг 3: Обучение инструментов
        tools_to_train = [step.selected_tool for step in context.execution_steps]
        
        # Добавление в датасет
        self._training.add_execution_to_dataset(context, [feedback])
        
        # Обучение каждого инструмента
        improvements = {}
        
        for tool in tools_to_train:
            old_reputation = tool.metadata.reputation
            
            # Обновление через Policy Gradient
            self._training.update_tool(
                tool=tool,
                task_embedding=context.task_embedding,
                feedbacks=[feedback]
            )
            
            new_reputation = tool.metadata.reputation
            delta = new_reputation - old_reputation
            
            improvements[tool.metadata.tool_name] = delta
            
            logger.debug(
                f"Tool updated: {tool.metadata.tool_name} "
                f"rep {old_reputation:.3f} → {new_reputation:.3f} (Δ{delta:+.4f})"
            )
        
        # Результат обучения
        result = RLAIFTrainingResult(
            evaluations_count=1,
            average_score=score.overall_score,
            tools_updated=len(tools_to_train),
            improvements=improvements
        )
        
        return result
    
    def batch_evaluate_and_train(
        self,
        executions: List[tuple]  # [(context, task, result), ...]
    ) -> RLAIFTrainingResult:
        """
        Batch оценка и обучение на нескольких выполнениях.
        
        Args:
            executions: Список кортежей (context, task_description, result)
            
        Returns:
            Агрегированный результат обучения
        """
        total_score = 0.0
        total_updated = 0
        all_improvements = {}
        
        for context, task, result in executions:
            train_result = self.evaluate_and_train(context, task, result)
            
            total_score += train_result.average_score
            total_updated += train_result.tools_updated
            
            # Объединение улучшений
            for tool_name, delta in train_result.improvements.items():
                if tool_name not in all_improvements:
                    all_improvements[tool_name] = []
                all_improvements[tool_name].append(delta)
        
        # Агрегация
        avg_score = total_score / len(executions) if executions else 0.0
        
        # Средние улучшения по каждому инструменту
        avg_improvements = {
            tool_name: sum(deltas) / len(deltas)
            for tool_name, deltas in all_improvements.items()
        }
        
        result = RLAIFTrainingResult(
            evaluations_count=len(executions),
            average_score=avg_score,
            tools_updated=total_updated,
            improvements=avg_improvements
        )
        
        logger.info(
            f"Batch RLAIF training: {result.evaluations_count} evaluations, "
            f"avg_score={result.average_score:.2f}, updated={result.tools_updated}"
        )
        
        return result
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику оценок.
        
        Returns:
            Словарь со статистикой
        """
        if not self._evaluation_history:
            return {
                "total_evaluations": 0,
                "average_score": 0.0
            }
        
        total = len(self._evaluation_history)
        
        avg_overall = sum(s.overall_score for s in self._evaluation_history) / total
        avg_correctness = sum(s.correctness for s in self._evaluation_history) / total
        avg_completeness = sum(s.completeness for s in self._evaluation_history) / total
        avg_relevance = sum(s.relevance for s in self._evaluation_history) / total
        avg_clarity = sum(s.clarity for s in self._evaluation_history) / total
        
        return {
            "total_evaluations": total,
            "average_overall_score": avg_overall,
            "average_correctness": avg_correctness,
            "average_completeness": avg_completeness,
            "average_relevance": avg_relevance,
            "average_clarity": avg_clarity,
            "min_score": min(s.overall_score for s in self._evaluation_history),
            "max_score": max(s.overall_score for s in self._evaluation_history)
        }
