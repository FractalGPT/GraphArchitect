"""
Сервис обучения инструментов на основе пользовательской обратной связи.

Интегрирует TrainingOrchestrator из GraphArchitect для:
- Сбора обратной связи
- Обновления репутации инструментов
- Обновления эмбеддингов
- Получения статистики обучения
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

try:
    from grapharchitect_bridge import get_bridge, is_bridge_available
    from grapharchitect.services.execution.execution_context import ExecutionContext
    from grapharchitect.services.feedback.feedback_data import FeedbackData, FeedbackSource
    GRAPHARCHITECT_ENABLED = True
except ImportError:
    GRAPHARCHITECT_ENABLED = False


class TrainingService:
    """
    Сервис для управления обучением инструментов.
    
    Обрабатывает обратную связь от пользователей и автоматических критиков,
    обновляет репутацию и эмбеддинги инструментов.
    """
    
    def __init__(self):
        self.enabled = GRAPHARCHITECT_ENABLED and is_bridge_available()
        
        if self.enabled:
            self.bridge = get_bridge()
            print("✅ TrainingService активирован")
        else:
            self.bridge = None
            print("⚠️ TrainingService не активен (GraphArchitect не доступен)")
    
    async def submit_feedback(
        self,
        task_id: str,
        quality_score: float,
        comment: str = "",
        detailed_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Принять пользовательскую обратную связь.
        
        Args:
            task_id: ID задачи (UUID)
            quality_score: Оценка качества (0.0-1.0)
            comment: Комментарий пользователя
            detailed_scores: Детализированные оценки по критериям
        
        Returns:
            Информация об обновлении инструментов
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Training service не активен"
            }
        
        try:
            # Создаем FeedbackData
            feedback = FeedbackData(
                task_id=UUID(task_id),
                source=FeedbackSource.USER,
                quality_score=quality_score,
                comment=comment,
                detailed_scores=detailed_scores or {},
                success=quality_score >= 0.7
            )
            
            # Добавляем в feedback collector
            self.bridge.training.feedback_collector.add_feedback(feedback)
            
            print(f"  📝 Получена обратная связь для {task_id}: {quality_score:.2f}")
            
            # TODO: Получить ExecutionContext для обучения
            # Сейчас контексты не сохраняются, нужно добавить в repository
            
            return {
                "success": True,
                "message": "Обратная связь сохранена",
                "quality_score": quality_score
            }
        
        except Exception as e:
            print(f"  ❌ Ошибка при обработке feedback: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику обучения.
        
        Returns:
            Словарь со статистикой:
            - total_executions: количество выполнений
            - average_quality: средняя оценка
            - success_rate: процент успешных
            - average_time: среднее время
            - average_cost: средняя стоимость
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Training service не активен"
            }
        
        try:
            stats = self.bridge.get_training_statistics()
            
            return {
                "enabled": True,
                "total_executions": stats.total_executions,
                "average_quality": round(stats.average_quality, 3),
                "success_rate": round(stats.success_rate, 3),
                "average_execution_time": round(stats.average_execution_time, 3),
                "average_cost": round(stats.average_cost, 3)
            }
        
        except Exception as e:
            print(f"  ❌ Ошибка при получении статистики: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    async def get_tool_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить метрики конкретного инструмента.
        
        Args:
            agent_id: ID агента
        
        Returns:
            Метрики инструмента или None
        """
        if not self.enabled:
            return None
        
        try:
            tool = self.bridge.get_tool_by_agent_id(agent_id)
            
            if not tool:
                return None
            
            return {
                "agent_id": agent_id,
                "tool_name": tool.metadata.tool_name,
                "reputation": round(tool.metadata.reputation, 3),
                "mean_cost": round(tool.metadata.mean_cost, 3),
                "mean_time": round(tool.metadata.mean_time_answer, 3),
                "training_sample_size": tool.metadata.training_sample_size,
                "variance_estimate": round(tool.metadata.variance_estimate, 3),
                "quality_scores_count": len(tool.metadata.quality_scores),
                "has_embedding": tool.metadata.capabilities_embedding is not None
            }
        
        except Exception as e:
            print(f"  ❌ Ошибка при получении метрик: {e}")
            return None
    
    async def get_all_tools_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики всех инструментов.
        
        Returns:
            Словарь с метриками всех инструментов
        """
        if not self.enabled:
            return {
                "enabled": False,
                "tools": []
            }
        
        try:
            tools_metrics = []
            
            for tool in self.bridge.tools:
                if hasattr(tool, 'agent_id'):
                    metrics = await self.get_tool_metrics(tool.agent_id)
                    if metrics:
                        tools_metrics.append(metrics)
            
            # Сортируем по репутации (лучшие первыми)
            tools_metrics.sort(key=lambda x: x["reputation"], reverse=True)
            
            return {
                "enabled": True,
                "total_tools": len(tools_metrics),
                "tools": tools_metrics
            }
        
        except Exception as e:
            print(f"  ❌ Ошибка при получении метрик всех инструментов: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    async def train_on_dataset(self, quality_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Запустить обучение на накопленном датасете.
        
        Args:
            quality_threshold: Порог качества для фильтрации
        
        Returns:
            Результат обучения
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Training service не активен"
            }
        
        try:
            print(f"  🎓 Запуск обучения (порог качества: {quality_threshold})")
            
            # Обучаем на успешных выполнениях
            self.bridge.training.train_on_successful_executions(
                self.bridge.tools,
                quality_threshold=quality_threshold
            )
            
            # Обновляем эмбеддинги
            self.bridge.training.update_tool_embeddings(
                self.bridge.tools,
                quality_threshold=quality_threshold
            )
            
            # Получаем статистику
            stats = self.bridge.get_training_statistics()
            
            print(f"  ✅ Обучение завершено")
            
            return {
                "success": True,
                "message": "Обучение завершено успешно",
                "statistics": {
                    "total_executions": stats.total_executions,
                    "average_quality": round(stats.average_quality, 3),
                    "success_rate": round(stats.success_rate, 3)
                }
            }
        
        except Exception as e:
            print(f"  ❌ Ошибка при обучении: {e}")
            return {
                "success": False,
                "message": str(e)
            }


# Singleton instance
_training_service: Optional[TrainingService] = None


def get_training_service() -> TrainingService:
    """Получить экземпляр TrainingService (singleton)"""
    global _training_service
    
    if _training_service is None:
        _training_service = TrainingService()
    
    return _training_service
