from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

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
    return {"response": f"{get_simple_answer(message)}"}


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        # Заглушка анализа
        return {"analysis": {"diagnosis": "Пример диагноза", "confidence": 0.85}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
