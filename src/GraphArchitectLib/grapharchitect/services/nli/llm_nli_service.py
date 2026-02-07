"""
LLM-based NLI сервис.

Использует LLM (OpenRouter, VLLM, DeepSeek) для парсинга естественного языка
в пару коннекторов (входной, выходной).

Алгоритм:
1. Поиск похожих примеров через k-NN
2. Формирование few-shot промпта (2-4 примера из k-NN)
3. Вызов LLM для получения коннекторов
4. Парсинг JSON ответа
"""

import logging
from typing import List, Optional, Dict, Any
import json
import os

from ...entities.base_tool import BaseTool
from ...entities.connectors.task_representation import TaskRepresentation
from ...entities.connectors.connector import Connector
from ..embedding.embedding_service import EmbeddingService
from .nli_dataset_item import NLIDatasetItem
from .natural_language_interface import NLIParseResult

logger = logging.getLogger(__name__)


class LLMNLIService:
    """
    NLI сервис на основе LLM.
    
    Использует LLM для точного парсинга с few-shot примерами из k-NN.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        backend: str = "openrouter",  # "openrouter", "vllm", "deepseek"
        model_name: str = "openai/gpt-3.5-turbo",
        api_key: Optional[str] = None,
        vllm_host: Optional[str] = None,
        k_similar: int = 3,
        temperature: float = 0.1
    ):
        """
        Инициализация LLM NLI.
        
        Args:
            embedding_service: Сервис эмбеддингов для k-NN
            backend: Бэкенд LLM ("openrouter", "vllm", "deepseek")
            model_name: Название модели
            api_key: API ключ (для OpenRouter/DeepSeek)
            vllm_host: URL VLLM сервера
            k_similar: Количество похожих примеров для few-shot
            temperature: Температура генерации (низкая для точности)
        """
        self._embedding_service = embedding_service
        self._backend = backend
        self._model_name = model_name
        self._k_similar = k_similar
        self._temperature = temperature
        
        # Датасет примеров
        self._dataset: List[NLIDatasetItem] = []
        
        # Инициализация LLM бэкенда
        self._llm = None
        self._init_backend(api_key, vllm_host)
        
        logger.info(f"LLM NLI initialized: {backend} with {model_name}")
    
    def _init_backend(self, api_key: Optional[str], vllm_host: Optional[str]):
        """Инициализация LLM бэкенда."""
        
        if self._backend == "openrouter":
            from ...tools.ApiTools.OpenRouterTool.openrouter_llm import OpenRouterLLM
            
            self._llm = OpenRouterLLM(
                api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
                model_name=self._model_name,
                system_prompt="You are an expert at parsing task descriptions into structured connectors."
            )
            
            logger.info("OpenRouter backend initialized")
        
        elif self._backend == "vllm":
            from ...tools.ApiTools.VLLMTool.VLLMApi import VLLMApi
            
            vllm_host = vllm_host or os.getenv("VLLM_HOST", "http://localhost:8000")
            
            self._llm = VLLMApi(
                vllm_host=vllm_host,
                model_name=self._model_name,
                system_prompt="You are an expert at parsing task descriptions."
            )
            
            logger.info(f"VLLM backend initialized: {vllm_host}")
        
        elif self._backend == "deepseek":
            from ...tools.ApiTools.DeepSeekTool import DeepSeekApi
            
            self._llm = DeepSeekApi(
                api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
                model_name=self._model_name or "deepseek-chat"
            )
            
            logger.info("DeepSeek backend initialized")
        
        else:
            raise ValueError(f"Unknown backend: {self._backend}")
    
    def load_dataset(self, examples: List[NLIDatasetItem]):
        """
        Загрузить датасет примеров для few-shot.
        
        Args:
            examples: Список примеров NLI
        """
        self._dataset = examples
        logger.info(f"Loaded {len(examples)} NLI examples")
    
    def parse_task(
        self,
        task_text: str,
        available_tools: List[BaseTool],
        k: int = 3
    ) -> NLIParseResult:
        """
        Распарсить задачу используя LLM с few-shot из k-NN.
        
        Алгоритм:
        1. Поиск k похожих примеров через k-NN
        2. Формирование few-shot промпта
        3. Вызов LLM
        4. Парсинг JSON ответа
        
        Args:
            task_text: Текст задачи на естественном языке
            available_tools: Доступные инструменты (для контекста)
            k: Количество примеров для few-shot
            
        Returns:
            NLIParseResult с коннекторами
        """
        if not task_text:
            return NLIParseResult(
                success=False,
                error_message="Task text cannot be empty"
            )
        
        # Шаг 1: Поиск похожих примеров через k-NN
        similar_examples = self._find_similar_examples(task_text, min(k, self._k_similar))
        
        # Шаг 2: Формирование промпта
        prompt = self._create_few_shot_prompt(task_text, similar_examples, available_tools)
        
        # Шаг 3: Вызов LLM
        try:
            response = self._call_llm(prompt)
            
            # Шаг 4: Парсинг ответа
            representation = self._parse_llm_response(response)
            
            if representation:
                logger.info(
                    f"LLM NLI parsed: {representation.input_connector.format} → "
                    f"{representation.output_connector.format}"
                )
                
                return NLIParseResult(
                    success=True,
                    task_representation=representation,
                    similar_examples=similar_examples if similar_examples else None,
                    confidence=0.85  # LLM обычно надежен
                )
            else:
                return NLIParseResult(
                    success=False,
                    error_message="Failed to parse LLM response"
                )
        
        except Exception as e:
            logger.error(f"Error in LLM NLI: {e}")
            return NLIParseResult(
                success=False,
                error_message=str(e)
            )
    
    def _find_similar_examples(self, task_text: str, k: int) -> List:
        """Поиск похожих примеров через k-NN."""
        
        if not self._dataset:
            return []
        
        # Эмбеддинг запроса
        query_emb = self._embedding_service.embed_text(task_text)
        
        # Вычисление сходства с каждым примером
        similarities = []
        
        for example in self._dataset:
            if example.task_embedding:
                sim = self._embedding_service.compute_similarity(
                    query_emb,
                    example.task_embedding
                )
                similarities.append((example, sim))
        
        # Сортировка и топ-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [ex for ex, sim in similarities[:k]]
    
    def _create_few_shot_prompt(
        self,
        task_text: str,
        similar_examples: List[NLIDatasetItem],
        available_tools: List[BaseTool]
    ) -> str:
        """
        Создать few-shot промпт для LLM.
        
        Структура:
        - Описание задачи
        - Few-shot примеры (из k-NN или базовые)
        - Доступные форматы
        - Задача пользователя
        """
        # Доступные форматы из инструментов
        available_formats = self._get_available_formats(available_tools)
        
        # Базовый промпт
        prompt = """Задача: Переведи описание задачи на естественном языке в формат входного и выходного коннектора.

Коннектор имеет формат: data_format|semantic_format

Доступные форматы:
"""
        
        # Добавляем доступные форматы
        prompt += "\n".join(f"  - {fmt}" for fmt in sorted(available_formats))
        
        prompt += "\n\nПримеры:\n\n"
        
        # Few-shot примеры
        if similar_examples:
            # Используем похожие из k-NN
            for i, example in enumerate(similar_examples[:4], 1):
                prompt += f"""Пример {i}:
Задача: "{example.task_text}"
Входной коннектор: {example.representation.input_connector.format}
Выходной коннектор: {example.representation.output_connector.format}

"""
        else:
            # Базовые примеры (если k-NN не нашел)
            prompt += """Пример 1:
Задача: "Классифицировать текст по категориям"
Входной коннектор: text|question
Выходной коннектор: text|category

Пример 2:
Задача: "Ответить на вопрос пользователя"
Входной коннектор: text|question
Выходной коннектор: text|answer

"""
        
        # Задача пользователя
        prompt += f"""Теперь для задачи:
Задача: "{task_text}"

Ответь в формате JSON:
{{
  "input_connector": {{
    "data_format": "...",
    "semantic_format": "..."
  }},
  "output_connector": {{
    "data_format": "...",
    "semantic_format": "..."
  }}
}}"""
        
        return prompt
    
    def _get_available_formats(self, tools: List[BaseTool]) -> set:
        """Получить множество доступных форматов из инструментов."""
        formats = set()
        
        for tool in tools:
            formats.add(tool.input.format)
            formats.add(tool.output.format)
        
        return formats
    
    def _call_llm(self, prompt: str) -> str:
        """
        Вызвать LLM для получения коннекторов.
        
        Args:
            prompt: Промпт с задачей
            
        Returns:
            Ответ LLM
        """
        if self._backend in ["openrouter", "vllm", "deepseek"]:
            response = self._llm.query_llm(
                question=prompt,
                temperature=self._temperature,
                max_tokens=300
            )
            return response
        else:
            raise ValueError(f"Unknown backend: {self._backend}")
    
    def _parse_llm_response(self, response: str) -> Optional[TaskRepresentation]:
        """
        Распарсить JSON ответ от LLM.
        
        Args:
            response: Ответ от LLM
            
        Returns:
            TaskRepresentation или None
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
            
            # Извлечение коннекторов
            input_conn = Connector(
                data['input_connector']['data_format'],
                data['input_connector']['semantic_format']
            )
            
            output_conn = Connector(
                data['output_connector']['data_format'],
                data['output_connector']['semantic_format']
            )
            
            # Создание представления
            representation = TaskRepresentation()
            representation.input_connector = input_conn
            representation.output_connector = output_conn
            
            return representation
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response: {response}")
            return None
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        Проверить доступность LLM.
        
        Returns:
            True если LLM готов к использованию
        """
        return self._llm is not None
