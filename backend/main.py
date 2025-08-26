from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/prices")
def get_prices():
    symbol = "COCAUSDT"  # пример COCA
    url = f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return {"symbol": symbol, "price": float(data["price"])}
    except Exception as e:
        return {"error": str(e)}
