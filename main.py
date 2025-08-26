from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Абсолютный путь к текущей папке
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Монтируем текущую папку как статическую
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
