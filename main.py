from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import subprocess

app = FastAPI()

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.api_route("/webhook", methods=["POST"])
async def webhook(request: Request):
    payload = await request.json()
    if payload.get("ref") == "refs/heads/main":
        subprocess.Popen(["/bin/bash", "deploy.sh"])
    return {"status": "ok"}
