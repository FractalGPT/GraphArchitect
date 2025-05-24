from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Optional

from Demo.DoctorDemo.Logic.main_logic import get_simple_answer

app = FastAPI(title="AI Therapist Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/web/static", StaticFiles(directory="web/static"), name="static")


@app.get("/")
def read_index():
    return FileResponse("web/index.html")


@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        # Здесь ваша логика обработки сообщения
        response = get_simple_answer(message)
        return JSONResponse(content={"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-image")
async def upload_image(
        file: UploadFile = File(...),
        message: Optional[str] = Form(None)
):
    try:
        content = await file.read()

        # 1. Анализ изображения (ваша реализация)
        image_analysis = {
            "diagnosis": "Пример диагноза по изображению",
            "confidence": 0.85
        }

        # 2. Если есть текстовое сообщение, обрабатываем и его
        text_response = None
        if message:
            text_response = get_simple_answer(message)

        # Формируем ответ
        result = {
            "analysis": image_analysis,
            "text_response": text_response
        }

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)