from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Главная страница
@app.get("/")
async def root():
    return FileResponse("index.html")
