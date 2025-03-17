from dotenv import load_dotenv
import os

from graph_architect.Tools.ApiTools.VLLMTool.VLLMApi import VLLMApi

# Загрузка конфигураций
load_dotenv()
host = os.getenv("HOST_VLLM")
model_name = os.getenv("MODEL_NAME")
system_prompt = os.getenv("SYSTEM_PROMPT")


vllm_client = VLLMApi(host, model_name, system_prompt)

def get_simple_answer(query):
    '''Запрос к vllm'''
    prompt_q = f"Инструкция. Доброжелательно консультируй пользователя. Ответь на вопрос {query}, если он задан по продуктам проекта FractalAgents AI от компании \"Аватар Машина\""
    prompt_q += f"Если запрос {query} связан с личностью бота ответь на только на базе этой информации \n\n\n {about_me}.\n\n\n Не пиши лишней информации. И не повторяй вопрос, пиши только ответ. Не используй MarkDown. Перефразируй ответ. Отвечай только на русском. Обращайся уважительно и на Вы."

    return vllm_client.query_llm(prompt_q)













about_me = ''''Этот бот является агентом-консультантам по продуктам компании "АватарМашина"'''