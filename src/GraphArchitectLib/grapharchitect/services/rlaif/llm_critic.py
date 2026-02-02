"""
LLM Critic для оценки качества ответов (RLAIF).

Reinforcement Learning from AI Feedback:
- Использует LLM как судью для оценки ответов
- Поддержка VLLM (локально) и OpenRouter (API)
- Структурированная оценка с баллами
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class LLMCriticScore:
    """
    Оценка от LLM критика.
    
    Содержит:
    - Общий балл качества (0-1)
    - Детализированные оценки
    - Обоснование
    - Рекомендации
    """
    
    overall_score: float  # 0.0-1.0
    
    # Детализированные оценки
    correctness: float = 0.0      # Правильность (0-1)
    completeness: float = 0.0     # Полнота (0-1)
    relevance: float = 0.0        # Релевантность (0-1)
    clarity: float = 0.0          # Ясность (0-1)
    
    # Текстовое обоснование
    reasoning: str = ""
    
    # Предложения по улучшению
    suggestions: str = ""
    
    # Метаданные
    critic_type: str = "llm"      # llm, rule-based, human
    model_used: str = ""


class LLMCritic:
    """
    LLM судья для оценки качества ответов.
    
    Использует либо VLLM (локально) либо OpenRouter (API)
    для оценки ответов цепочки выполнения.
    """
    
    def __init__(
        self,
        backend: str = "openrouter",  # "openrouter" или "vllm"
        model_name: str = "openai/gpt-4",
        vllm_host: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        temperature: float = 0.2,
        detailed_evaluation: bool = True
    ):
        """
        Инициализация LLM критика.
        
        Args:
            backend: Бэкенд для LLM ("openrouter" или "vllm")
            model_name: Название модели
            vllm_host: URL VLLM сервера (для backend="vllm")
            openrouter_api_key: API ключ OpenRouter
            temperature: Температура генерации (низкая для consistency)
            detailed_evaluation: Детальная оценка по критериям
        """
        self._backend = backend
        self._model_name = model_name
        self._temperature = temperature
        self._detailed_evaluation = detailed_evaluation
        
        # Инициализация бэкенда
        if backend == "openrouter":
            self._init_openrouter(openrouter_api_key)
        elif backend == "vllm":
            self._init_vllm(vllm_host)
        else:
            raise ValueError(f"Unknown backend: {backend}. Use 'openrouter' or 'vllm'")
        
        logger.info(f"LLM Critic initialized: {backend} with {model_name}")
    
    def _init_openrouter(self, api_key: Optional[str]):
        """Инициализация OpenRouter бэкенда."""
        try:
            from ...tools.ApiTools.OpenRouterTool.openrouter_llm import OpenRouterLLM
            
            self._llm = OpenRouterLLM(
                api_key=api_key,
                model_name=self._model_name,
                system_prompt="You are an expert AI critic evaluating task completion quality."
            )
            
            logger.info("OpenRouter backend initialized")
        
        except ImportError as e:
            logger.error(f"Failed to import OpenRouterLLM: {e}")
            raise
    
    def _init_vllm(self, vllm_host: Optional[str]):
        """Инициализация VLLM бэкенда."""
        if not vllm_host:
            vllm_host = os.getenv("VLLM_HOST", "http://localhost:8000")
        
        try:
            from ...tools.ApiTools.VLLMTool.VLLMApi import VLLMApi
            
            self._llm = VLLMApi(
                vllm_host=vllm_host,
                model_name=self._model_name,
                prompt="You are an expert AI critic evaluating task completion quality."
            )
            
            logger.info(f"VLLM backend initialized: {vllm_host}")
        
        except ImportError as e:
            logger.error(f"Failed to import VLLMApi: {e}")
            raise
    
    def evaluate_answer(
        self,
        task: str,
        answer: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMCriticScore:
        """
        Оценить качество ответа на задачу.
        
        Args:
            task: Исходная задача (текст)
            answer: Ответ цепочки инструментов
            context: Дополнительный контекст (опционально)
                - execution_time: время выполнения
                - tools_used: использованные инструменты
                - cost: стоимость
                
        Returns:
            LLMCriticScore с оценками
        """
        # Формирование промпта для оценки
        evaluation_prompt = self._create_evaluation_prompt(task, answer, context)
        
        try:
            # Вызов LLM
            response = self._call_llm(evaluation_prompt)
            
            # Парсинг ответа
            score = self._parse_evaluation_response(response)
            
            if score:
                score.model_used = self._model_name
                logger.info(
                    f"LLM Critic evaluated: overall={score.overall_score:.2f}, "
                    f"correct={score.correctness:.2f}"
                )
            
            return score
        
        except Exception as e:
            logger.error(f"Error in LLM evaluation: {e}")
            
            # Fallback - нейтральная оценка
            return LLMCriticScore(
                overall_score=0.5,
                correctness=0.5,
                completeness=0.5,
                relevance=0.5,
                clarity=0.5,
                reasoning=f"Error during evaluation: {str(e)}",
                model_used=self._model_name
            )
    
    def _create_evaluation_prompt(
        self,
        task: str,
        answer: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Создать промпт для оценки качества.
        
        Структурированный промпт с критериями оценки.
        """
        context = context or {}
        
        # Базовый промпт
        prompt = f"""Вы - эксперт по оценке качества ответов AI систем.

ЗАДАЧА:
{task}

ОТВЕТ СИСТЕМЫ:
{answer}
"""
        
        # Дополнительный контекст
        if context:
            prompt += "\n\nКОНТЕКСТ ВЫПОЛНЕНИЯ:\n"
            
            if 'execution_time' in context:
                prompt += f"- Время выполнения: {context['execution_time']:.2f}s\n"
            
            if 'tools_used' in context:
                tools_str = ", ".join(context['tools_used'])
                prompt += f"- Использованные инструменты: {tools_str}\n"
            
            if 'cost' in context:
                prompt += f"- Стоимость: ${context['cost']:.4f}\n"
        
        # Критерии оценки
        if self._detailed_evaluation:
            prompt += """

ОЦЕНИТЕ ОТВЕТ ПО СЛЕДУЮЩИМ КРИТЕРИЯМ (шкала 0-10):

1. ПРАВИЛЬНОСТЬ (Correctness):
   - Ответ корректно решает задачу?
   - Нет фактических ошибок?
   - Логически последователен?

2. ПОЛНОТА (Completeness):
   - Ответ полностью покрывает задачу?
   - Все аспекты рассмотрены?
   - Нет упущений?

3. РЕЛЕВАНТНОСТЬ (Relevance):
   - Ответ релевантен задаче?
   - Нет лишней информации?
   - Фокус на главном?

4. ЯСНОСТЬ (Clarity):
   - Ответ понятен?
   - Хорошо структурирован?
   - Легко читается?

ФОРМАТ ОТВЕТА (обязательно JSON):
{
  "correctness": <балл 0-10>,
  "completeness": <балл 0-10>,
  "relevance": <балл 0-10>,
  "clarity": <балл 0-10>,
  "overall": <балл 0-10>,
  "reasoning": "Краткое обоснование оценок",
  "suggestions": "Предложения по улучшению (если есть)"
}
"""
        else:
            # Простая оценка
            prompt += """

ОЦЕНИТЕ ОБЩЕЕ КАЧЕСТВО ОТВЕТА (шкала 0-10):
- Насколько хорошо ответ решает задачу?

ФОРМАТ ОТВЕТА (обязательно JSON):
{
  "overall": <балл 0-10>,
  "reasoning": "Краткое обоснование"
}
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Вызвать LLM для получения оценки.
        
        Args:
            prompt: Промпт для оценки
            
        Returns:
            Ответ LLM
        """
        if self._backend == "openrouter":
            response = self._llm.query_llm(
                question=prompt,
                temperature=self._temperature,
                max_tokens=500
            )
            return response
        
        elif self._backend == "vllm":
            response = self._llm.query_llm(
                question=prompt,
                temperature=self._temperature,
                max_tokens=500
            )
            return response
        
        else:
            raise ValueError(f"Unknown backend: {self._backend}")
    
    def _parse_evaluation_response(self, response: str) -> Optional[LLMCriticScore]:
        """
        Распарсить ответ LLM и извлечь оценки.
        
        Args:
            response: Ответ от LLM
            
        Returns:
            LLMCriticScore или None
        """
        try:
            # Ищем JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON found in LLM response")
                logger.debug(f"Response: {response}")
                return None
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Извлечение оценок
            if self._detailed_evaluation:
                # Детальные оценки (0-10 → 0-1)
                correctness = data.get('correctness', 5.0) / 10.0
                completeness = data.get('completeness', 5.0) / 10.0
                relevance = data.get('relevance', 5.0) / 10.0
                clarity = data.get('clarity', 5.0) / 10.0
                overall = data.get('overall', 5.0) / 10.0
            else:
                # Простая оценка
                overall = data.get('overall', 5.0) / 10.0
                correctness = overall
                completeness = overall
                relevance = overall
                clarity = overall
            
            # Создание результата
            score = LLMCriticScore(
                overall_score=overall,
                correctness=correctness,
                completeness=completeness,
                relevance=relevance,
                clarity=clarity,
                reasoning=data.get('reasoning', ''),
                suggestions=data.get('suggestions', ''),
                critic_type="llm",
                model_used=self._model_name
            )
            
            return score
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {e}")
            logger.debug(f"Response: {response}")
            return None
        
        except Exception as e:
            logger.error(f"Error parsing evaluation: {e}")
            return None
    
    def batch_evaluate(
        self,
        tasks_and_answers: list
    ) -> list:
        """
        Batch оценка нескольких пар задача-ответ.
        
        Args:
            tasks_and_answers: Список кортежей (task, answer, context)
            
        Returns:
            Список LLMCriticScore
        """
        scores = []
        
        for item in tasks_and_answers:
            if len(item) == 2:
                task, answer = item
                context = None
            else:
                task, answer, context = item
            
            score = self.evaluate_answer(task, answer, context)
            scores.append(score)
        
        logger.info(f"Batch evaluated {len(scores)} answers")
        return scores
