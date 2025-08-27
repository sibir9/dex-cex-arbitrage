from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

# 👉 Главная страница (отдаём index.html)
@app.get("/")
async def root():
    return FileResponse("index.html")

# 👉 GitHub Webhook для автообновления
@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    # Проверяем, что пуш был в ветку main
    if payload.get("ref") == "refs/heads/main":
        subprocess.Popen(["/bin/bash", "deploy.sh"])
    return {"status": "ok"}
