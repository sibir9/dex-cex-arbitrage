from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import json

app = FastAPI()

# Путь к папке public
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "..", "public")

# Монтируем public как статические файлы
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

# Пример API
@app.get("/prices")
def get_prices():
    # Загружаем токены
    with open(os.path.join(BASE_DIR, "..", "tokens.json")) as f:
        tokens = json.load(f)
    return {"tokens": tokens, "example_price": 123.45}
