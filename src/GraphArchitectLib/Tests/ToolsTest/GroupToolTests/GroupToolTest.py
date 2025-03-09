import numpy as np

from graph_architect.BaseTool import BaseIntTool
from graph_architect.ToolRouters.ToolGroup.ToolChain import ToolChainBase

# Эмуляция инструмента
class MockTool(BaseIntTool):

    def processing(self, command: str):
        return f"{self.tool_id} {command}" # Эмуляция выполнения

    def calc_cost(self, input_data) -> float:
        return self.tool_id % len(input_data) # Эмуляция разной стоимости задачи

    def calc_loss(self):
        return 0.1

# Тестирование цепочки
tools = []

tasks = ["qa", "rag"]


for i in range(1, 1000):
    tool = MockTool(
        tool_id=10 + i, tool_name="llm",
        tool_description="llm1",
        input_data_format="str",
        input_semantic_format="q",
        output_data_format="str",
        output_semantic_format="answer",
        task_type=np.random.choice(tasks))

    tools.append(tool)

chain = ToolChainBase()

result = chain.tool_chain_run("Привет", ["rag", "rag", "rag", "qa"], tools)
print(result)
