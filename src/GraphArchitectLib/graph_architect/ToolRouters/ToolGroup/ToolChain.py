class ToolChainBase:
    def __init__(self):
        pass

    def tool_chain_run(self, input_data, task_chain, tools, min_q=0):
        """Запуск цепочки инструментов

        Аргументы:
        input_data -- входные данные
        task_chain -- список задач в цепочке
        tools -- список доступных инструментов
        min_q -- минимальный порог качества выполнения инструмента

        Возвращает:
        Словарь с ключом 'executed' (bool) и, если успешно, 'result' (данные после обработки)
        """
        next_data = input_data
        tool_matrix = self._generate_tool_matrix(task_chain, tools)

        if not tool_matrix['matrix_created']:
            return {"executed": False}

        # Выполняем каждую задачу по очереди
        for task in task_chain:
            next_data = self._execute_task(next_data, tool_matrix['task_tools'][task], min_q)
            if not next_data["executed"]:
                return {"executed": False}

        return {"executed": True, "result": next_data}

    def _execute_task(self, input_data, tool_list, min_q):
        """Выполняет задачу, выбирая лучший инструмент по качеству

        Аргументы:
        input_data -- входные данные
        tool_list -- список инструментов, соответствующих задаче
        min_q -- минимальный порог качества выполнения инструмента

        Возвращает:
        Словарь с ключом 'executed' (bool) и, если успешно, 'result' (результат работы инструмента)
        """
        # Инструмент с максимальным значением get_q(input_data)
        best_tool = max(tool_list, key=lambda tool: tool.get_q(input_data), default=None)

        # Превышает ли качество минимальный порог
        if best_tool and best_tool.get_q(input_data) >= min_q:
            return {"executed": True, "result": best_tool.run(input_data)}

        return {"executed": False}

    def _generate_tool_matrix(self, task_chain, tools):
        """Генерирует матрицу инструментов, привязывая инструменты к задачам

        Аргументы:
        task_chain -- список задач в цепочке
        tools -- список доступных инструментов

        Возвращает:
        Словарь с флагом 'matrix_created' (bool) и словарем 'task_tools',
        содержащим задачи и соответствующие им инструменты
        """
        task_tools = {task: [] for task in task_chain}

        for tool in tools:
            if tool.task in task_tools:
                task_tools[tool.task].append(tool)

        # Содержит ли каждый шаг хотя бы один инструмент
        matrix_created = all(task_tools[task] for task in task_chain)

        return {'matrix_created': matrix_created, 'task_tools': task_tools}