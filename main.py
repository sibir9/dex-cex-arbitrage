from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

# Главная страница
@app.get("/")
async def root():
    return FileResponse("index.html")

# Webhook для GitHub — только POST
@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        if payload.get("ref") == "refs/heads/main":
            subprocess.Popen(["/bin/bash", "deploy.sh"])
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
