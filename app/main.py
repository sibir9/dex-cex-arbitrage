from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "..", "public")

# Монтируем папку public под /static (для любых статических файлов)
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")

# Главная страница
@app.get("/")
def root():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))
