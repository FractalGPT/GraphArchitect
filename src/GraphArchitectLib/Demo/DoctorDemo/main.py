from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn
import os
import json
import requests




app = FastAPI(title="AI Therapist Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Загрузка конфигураций
load_dotenv()
host = os.getenv("HOST_VLLM")
model_name = os.getenv("MODEL_NAME")


@app.get("/")
def read_index():
    return FileResponse("index.html")

# Пример POST-эндпоинта для чата
@app.post("/chat")
async def chat(message: str = Form(...)):
    # Заглушка логики AI-терапевта
    return {"response": f"AI ответ: {query_llm(message)}"}

# Пример POST-эндпоинта для загрузки и анализа изображения
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        # Заглушка анализа
        return {"analysis": {"diagnosis": "Пример диагноза", "confidence": 0.85}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# Отправка в ллм
def query_llm(question):

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "repetition_penalty": 1.06,
        "top_p": 0.95,
        "top_k": 30,
        "stream": False,
        "temperature": 0.20,
        "max_tokens": 7000,
        "messages": [
            {"role": "system", "content": "Интеллектуальный помощник для диагностики различных заболеваний. Виртуальный терапевт. Даешь рекомендации к кому обратиться, какому врачу и какие анализы досдать. Ты сам не ставишь диагноз, а только рекомендуешь к кому обратиться (кроме терапевта). Ты как замена терапевта."},
            {"role": "user", "content": question}
        ],
        "model": model_name
    }

    response = requests.post(host, headers=headers, data=json.dumps(payload))
    ans = response.json()
    return ans['choices'][0]['message']['content']




# Точка входа
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
