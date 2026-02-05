"""
ReWOO Planner - Reasoning Without Observation.

Подход ReWOO:
1. Получаем цепочки от графового алгоритма
2. Отправляем в LLM для создания детального плана
3. Выполняем по плану (без промежуточных наблюдений)

Используется Gemini 3 Flash для быстрого планирования.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class ReWOOStep:
    """Шаг в ReWOO плане."""
    
    step_id: str
    tool_name: str
    description: str
    depends_on: List[str]  # ID шагов, от которых зависит
    expected_output: str


@dataclass
class ReWOOPlan:
    """Полный план ReWOO."""
    
    steps: List[ReWOOStep]
    reasoning: str  # Обоснование плана от LLM
    estimated_time: float
    estimated_cost: float


class ReWOOPlanner:
    """
    ReWOO планировщик.
    
    Использует LLM для создания детального плана выполнения
    на основе цепочек от графового алгоритма.
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        fallback_to_openrouter: bool = True
    ):
        """
        Инициализация планировщика.
        
        Args:
            gemini_api_key: API ключ Gemini (или GEMINI_API_KEY из env)
            model: Модель (gemini-1.5-flash рекомендуется)
            fallback_to_openrouter: Использовать OpenRouter если Gemini недоступен
        """
        self._gemini_key = gemini_api_key
        self._model = model
        self._fallback_to_openrouter = fallback_to_openrouter
        self._llm = None
        
        # Инициализация LLM
        self._init_llm()
        
        logger.info(f"ReWOO Planner initialized with {model}")
    
    def _init_llm(self):
        """Инициализация LLM для планирования."""
        
        import os
        
        # Попытка использовать Gemini через OpenRouter
        try:
            from ...tools.ApiTools.OpenRouterTool.openrouter_llm import OpenRouterLLM
            
            # Gemini через OpenRouter
            self._llm = OpenRouterLLM(
                model_name="google/gemini-1.5-flash",
                system_prompt="You are an expert planner for multi-step task execution."
            )
            
            logger.info("ReWOO using Gemini 1.5 Flash via OpenRouter")
        
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            
            if self._fallback_to_openrouter:
                # Fallback на GPT-3.5
                try:
                    from ...tools.ApiTools.OpenRouterTool.openrouter_llm import OpenRouterLLM
                    
                    self._llm = OpenRouterLLM(
                        model_name="openai/gpt-3.5-turbo",
                        system_prompt="You are an expert planner."
                    )
                    
                    logger.warning("Fallback to GPT-3.5-turbo for ReWOO planning")
                except:
                    pass
    
    def create_plan(
        self,
        task_description: str,
        strategies: List[List],  # Цепочки от графового алгоритма
        algorithm_used: str
    ) -> Optional[ReWOOPlan]:
        """
        Создать детальный план выполнения.
        
        Args:
            task_description: Описание задачи
            strategies: Цепочки инструментов от графового алгоритма
            algorithm_used: Использованный алгоритм (yen_5, dijkstra, etc.)
            
        Returns:
            ReWOOPlan или None
        """
        if not self._llm:
            logger.error("LLM not available for ReWOO planning")
            return None
        
        if not strategies:
            logger.error("No strategies provided")
            return None
        
        # Формируем промпт для планирования
        prompt = self._create_planning_prompt(task_description, strategies, algorithm_used)
        
        try:
            # Вызов LLM
            response = self._llm.query_llm(
                question=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Парсинг плана
            plan = self._parse_plan_from_response(response, strategies)
            
            if plan:
                logger.info(f"ReWOO plan created: {len(plan.steps)} steps")
            
            return plan
        
        except Exception as e:
            logger.error(f"Error creating ReWOO plan: {e}")
            return None
    
    def _create_planning_prompt(
        self,
        task_description: str,
        strategies: List[List],
        algorithm: str
    ) -> str:
        """
        Создать промпт для планирования.
        
        Включает:
        - Описание задачи
        - Найденные цепочки инструментов
        - Требование создать детальный план
        """
        prompt = f"""Задача: Создать детальный план выполнения для задачи.

ЗАДАЧА ПОЛЬЗОВАТЕЛЯ:
{task_description}

НАЙДЕННЫЕ ЦЕПОЧКИ ИНСТРУМЕНТОВ (от {algorithm}):
"""
        
        # Добавляем все найденные цепочки
        for i, strategy in enumerate(strategies[:5], 1):  # Топ-5
            tool_names = [
                t.metadata.tool_name if hasattr(t, 'metadata') else str(t)
                for t in strategy
            ]
            chain_str = " → ".join(tool_names)
            prompt += f"\n  Цепочка {i}: {chain_str}"
        
        prompt += """

ТВОЯ ЗАДАЧА:
Создай детальный план выполнения (ReWOO approach):
1. Выбери оптимальную цепочку (или комбинацию)
2. Опиши что делает каждый шаг
3. Укажи зависимости между шагами
4. Оцени время и стоимость

ФОРМАТ ОТВЕТА (обязательно JSON):
{
  "reasoning": "Почему выбрана эта стратегия...",
  "steps": [
    {
      "step_id": "step-1",
      "tool_name": "Classifier",
      "description": "Classify the input text",
      "depends_on": [],
      "expected_output": "Category label"
    },
    {
      "step_id": "step-2", 
      "tool_name": "Responder",
      "description": "Generate response based on category",
      "depends_on": ["step-1"],
      "expected_output": "Response text"
    }
  ],
  "estimated_time": 3.5,
  "estimated_cost": 0.05
}
"""
        
        return prompt
    
    def _parse_plan_from_response(
        self,
        response: str,
        original_strategies: List[List]
    ) -> Optional[ReWOOPlan]:
        """
        Распарсить план из ответа LLM.
        
        Args:
            response: Ответ от LLM
            original_strategies: Оригинальные цепочки (для fallback)
            
        Returns:
            ReWOOPlan или None
        """
        try:
            # Извлечение JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON in ReWOO plan response")
                return self._create_fallback_plan(original_strategies[0])
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Создание шагов
            steps = []
            for step_data in data.get('steps', []):
                step = ReWOOStep(
                    step_id=step_data.get('step_id', f"step-{len(steps)}"),
                    tool_name=step_data.get('tool_name', 'Unknown'),
                    description=step_data.get('description', ''),
                    depends_on=step_data.get('depends_on', []),
                    expected_output=step_data.get('expected_output', '')
                )
                steps.append(step)
            
            plan = ReWOOPlan(
                steps=steps,
                reasoning=data.get('reasoning', ''),
                estimated_time=data.get('estimated_time', 5.0),
                estimated_cost=data.get('estimated_cost', 0.05)
            )
            
            return plan
        
        except Exception as e:
            logger.error(f"Error parsing ReWOO plan: {e}")
            
            # Fallback: создаем простой план из первой цепочки
            return self._create_fallback_plan(original_strategies[0])
    
    def _create_fallback_plan(self, strategy: List) -> ReWOOPlan:
        """
        Создать простой plan из цепочки (fallback).
        
        Args:
            strategy: Цепочка инструментов
            
        Returns:
            Базовый ReWOOPlan
        """
        steps = []
        
        for i, tool in enumerate(strategy):
            tool_name = tool.metadata.tool_name if hasattr(tool, 'metadata') else str(tool)
            
            step = ReWOOStep(
                step_id=f"step-{i}",
                tool_name=tool_name,
                description=f"Execute {tool_name}",
                depends_on=[f"step-{i-1}"] if i > 0 else [],
                expected_output="Result"
            )
            steps.append(step)
        
        return ReWOOPlan(
            steps=steps,
            reasoning="Fallback plan from graph strategy",
            estimated_time=len(steps) * 2.0,
            estimated_cost=len(steps) * 0.02
        )
