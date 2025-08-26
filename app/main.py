from fastapi import FastAPI
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Монтируем папку public как статическую
app.mount("/", StaticFiles(directory="public", html=True), name="public")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

with open("tokens.json") as f:
    TOKENS = json.load(f)

MEXC_FEE = 0.001
ODOS_FEE = 0.002
USDT_DECIMALS = 6

CHAIN_ID = 137
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"

def fetch_odos_price(token_address, usdt_amount=50):
    try:
        effective_usdt = usdt_amount * (1 - ODOS_FEE)
        resp = requests.post(
            "https://api.odos.xyz/sor/quote/v2",
            json={
                "chainId": CHAIN_ID,
                "inputTokens": [{"tokenAddress": USDT, "amount": str(int(effective_usdt * 10**USDT_DECIMALS))}],
                "outputTokens": [{"tokenAddress": token_address}],
                "slippageLimitPercent": 1
            },
            timeout=10
        ).json()
        out = resp.get("outAmounts", [None])[0]
        if out:
            tokens_bought = int(out)/1e18
            price_per_token = effective_usdt / tokens_bought
            return price_per_token, tokens_bought
        return None, None
    except:
        return None, None

def fetch_mexc_avg_price(symbol, tokens_amount):
    try:
        resp = requests.get(f"https://api.mexc.com/api/v3/depth?symbol={symbol}USDT&limit=50", timeout=10).json()
        asks = resp.get("asks", [])
        remaining = tokens_amount
        total_usdt = 0
        for price_str, qty_str in asks:
            price = float(price_str)
            qty = float(qty_str)
            if remaining >= qty:
                total_usdt += price*qty
                remaining -= qty
            else:
                total_usdt += price*remaining
                remaining = 0
                break
        if remaining > 0:
            return None
        return total_usdt / tokens_amount
    except:
        return None

@app.get("/prices")
def get_prices():
    result = {"odos": {}, "mexc": {}, "spread": {}, "profit": {}}
    for token in TOKENS:
        odos_price, tokens_bought = fetch_odos_price(token["address"])
        mexc_price = None
        profit = None
        if tokens_bought:
            mexc_price = fetch_mexc_avg_price(token["symbol"], tokens_bought)
            if mexc_price:
                usdt_received = tokens_bought * mexc_price * (1 - MEXC_FEE)
                profit = usdt_received - 50
        result["odos"][token["symbol"]] = odos_price
        result["mexc"][token["symbol"]] = mexc_price
        result["profit"][token["symbol"]] = profit
        if odos_price and mexc_price:
            result["spread"][token["symbol"]] = (mexc_price - odos_price)/odos_price*100
    return result
