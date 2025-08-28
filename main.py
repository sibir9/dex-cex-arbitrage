# main.py
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import subprocess
from dex_cex_polygon import get_all_prices

app = FastAPI()

# === Главная страница ===
@app.get("/")
async def root():
    return FileResponse(
        "index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# === GitHub Webhook (автодеплой) ===
@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        if payload.get("ref") == "refs/heads/main":
            # Запускаем deploy.sh в фоне
            subprocess.Popen(["/bin/bash", "deploy.sh"])
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# === API для получения цены NAKA ===
@app.get("/price/naka")
def naka_price():
    all_prices = get_all_prices()
    return all_prices.get("NAKA", {})

# === Отдаём polygon.html ===
@app.get("/polygon")
def polygon_page():
    return FileResponse(
        "polygon.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# === API для получения цен всех токенов ===
@app.get("/price/all")
def all_prices():
    return get_all_prices()


# === Для локального запуска uvicorn ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)  # port можно изменить, если нужно



# version 4
