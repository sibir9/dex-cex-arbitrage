from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Монтируем public как статическую папку
app.mount("/", StaticFiles(directory="../public", html=True), name="public")



