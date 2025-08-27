from fastapi import FastAPI, Request
import subprocess

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    if payload.get("ref") == "refs/heads/main":  # следим за веткой main
        subprocess.Popen(["/bin/bash", "deploy.sh"])
    return {"status": "ok"}
