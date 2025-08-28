# dex_cex_polygon.py
import requests

NAKA_TOKEN = "0x311434160d7537be358930def317afb606c0d737"
CHAIN_ID = 137  # Polygon
USDT_TOKEN = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

def get_naka_prices():
    try:
        # === ODOS (DEX, Polygon) ===
        odos_url = "https://api.odos.xyz/sor/quote/v2"
        payload = {
            "chainId": CHAIN_ID,
            "inputTokens": [{"tokenAddress": NAKA_TOKEN, "amount": str(10**18)}],
            "outputTokens": [{"tokenAddress": USDT_TOKEN, "proportion": 1}],
            "slippageLimitPercent": 1,
            "userAddr": "0x000000000000000000000000000000000000dead",
            "referralCode": 0,
        }
        odos_resp = requests.post(odos_url, json=payload, timeout=10).json()
        odos_price = None
        if "outAmounts" in odos_resp and odos_resp["outAmounts"]:
            odos_price = int(odos_resp["outAmounts"][0]) / 1e6  # USDT = 6 decimals

        # === MEXC (CEX) ===
        mexc_url = "https://api.mexc.com/api/v3/ticker/price?symbol=NAKAUSDT"
        mexc_resp = requests.get(mexc_url, timeout=10).json()
        mexc_price = float(mexc_resp["price"]) if "price" in mexc_resp else None

        return {
            "odos_price_usdt": odos_price,
            "mexc_price_usdt": mexc_price,
            "error": None,
        }
    except Exception as e:
        return {"odos_price_usdt": None, "mexc_price_usdt": None, "error": str(e)}
