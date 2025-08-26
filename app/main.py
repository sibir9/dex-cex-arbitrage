from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Абсолютный путь к public
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# Монтируем папку public как статическую
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
