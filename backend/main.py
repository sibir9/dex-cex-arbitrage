
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

USDT_ADDRESS = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"
CHAIN_ID = 137

with open("tokens.json") as f:
    TOKENS = json.load(f)

@app.get("/prices/{symbol}")
def get_price(symbol: str):
    token = next((t for t in TOKENS if t["symbol"] == symbol), None)
    if not token:
        return {"error": "Token not found"}
    # MEXC
    try:
        res = requests.get(f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}USDT")
        mexc_price = float(res.json().get("price", 0))
    except:
        mexc_price = None
    # ODOS (simplified, returns None if fails)
    try:
        body = {
            "chainId": CHAIN_ID,
            "inputTokens":[{"tokenAddress": token["address"], "amount":"1000000000000000000"}],
            "outputTokens":[{"tokenAddress": USDT_ADDRESS}],
            "slippageLimitPercent":1
        }
        res = requests.post("https://api.odos.xyz/sor/quote/v2", json=body)
        odos_out = res.json().get("outAmounts",[None])[0]
        odos_price = float(odos_out)/1e6 if odos_out else None
    except:
        odos_price = None
    return {"mexc": mexc_price, "odos": odos_price}
