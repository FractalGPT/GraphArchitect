"""Расширитель инструментов для Any->Any семантики"""

from typing import List
from ..entities.base_tool import BaseTool
from ..entities.connectors.connector import ANY_SEMANTIC


class ToolExpander:
    """
    Расширитель инструментов.
    
    Создает дополнительные копии инструментов с Any->Any семантикой,
    подставляя конкретные семантики из контекста задачи.
    """
    
    def expand(
        self,
        tools: List[BaseTool],
        start_semantic: str,
        end_semantic: str
    ) -> List[BaseTool]:
        """
        Расширить список инструментов.
        
        Для инструментов с Any->Any семантикой создаются копии
        с конкретными семантиками входа и выхода.
        
        Args:
            tools: Исходный список инструментов
            start_semantic: Семантика входа задачи
            end_semantic: Семантика выхода задачи
            
        Returns:
            Расширенный список инструментов
        """
        expanded = list(tools)  # Копируем исходные
        
        for tool in tools:
            # Проверяем, нужно ли расширять
            input_sem = tool.input.semantic_format
            output_sem = tool.output.semantic_format
            
            # Any на входе
            if input_sem == ANY_SEMANTIC and start_semantic:
                clone = tool.clone()
                clone.input.input_semantic = start_semantic
                expanded.append(clone)
            
            # Any на выходе
            if output_sem == ANY_SEMANTIC and end_semantic:
                clone = tool.clone()
                clone.output.input_semantic = end_semantic
                expanded.append(clone)
            
            # Any на входе и выходе
            if (input_sem == ANY_SEMANTIC and 
                output_sem == ANY_SEMANTIC and 
                start_semantic and end_semantic):
                clone = tool.clone()
                clone.input.input_semantic = start_semantic
                clone.output.input_semantic = end_semantic
                expanded.append(clone)
        
        return expanded
