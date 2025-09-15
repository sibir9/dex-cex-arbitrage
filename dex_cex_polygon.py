import asyncio
import aiohttp
import json
import os
import time

CHAIN_ID = 137  # Polygon
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"
ODOS_FEE = 0.002
MEXC_FEE = 0.001

# Загружаем токены
TOKENS_FILE = os.path.join(os.path.dirname(__file__), "poltokens.json")
with open(TOKENS_FILE, "r") as f:
    TOKENS = json.load(f)

# Кэш цен
PRICE_CACHE = {}
CACHE_TTL = 10  # секунд
LAST_UPDATE = 0

async def fetch_odos_price(session, token):
    effective_usdt = 50 * (1 - ODOS_FEE)
    try:
        async with session.post(
            "https://api.odos.xyz/sor/quote/v2",
            json={
                "chainId": CHAIN_ID,
                "inputTokens": [{"tokenAddress": USDT, "amount": str(int(effective_usdt * 1e6))}],
                "outputTokens": [{"tokenAddress": token["address"]}],
                "slippageLimitPercent": 1
            },
            timeout=10
        ) as resp:
            data = await resp.json()
            out_amount = data.get("outAmounts", [None])[0]
            if out_amount:
                tokens_bought = int(out_amount) / 1e18
                return effective_usdt / tokens_bought
    except Exception as e:
        return f"ODOS error: {str(e)}"
    return None

async def fetch_mexc_price(session, token):
    symbol = token["symbol"]
    try:
        async with session.get(f"https://api.mexc.com/api/v3/depth?symbol={symbol}USDT&limit=50", timeout=10) as resp:
            data = await resp.json()
            bids = data.get("bids", [])
            if bids:
                # считаем среднюю цену для 50 токенов
                total_qty = 0
                total_cost = 0
                for price_str, qty_str in bids:
                    price = float(price_str)
                    qty = float(qty_str)
                    buy_qty = min(50 - total_qty, qty)
                    total_cost += buy_qty * price
                    total_qty += buy_qty
                    if total_qty >= 50:
                        break
                return total_cost / total_qty if total_qty > 0 else None
    except Exception as e:
        return f"MEXC error: {str(e)}"
    return None

async def update_prices():
    global PRICE_CACHE, LAST_UPDATE
    async with aiohttp.ClientSession() as session:
        tasks = []
        for token in TOKENS:
            tasks.append(fetch_token_prices(session, token))
        results = await asyncio.gather(*tasks)
        PRICE_CACHE = {token["symbol"]: res for token, res in results}
        LAST_UPDATE = time.time()

async def fetch_token_prices(session, token):
    odos = await fetch_odos_price(session, token)
    mexc = await fetch_mexc_price(session, token)
    return token, {
        "address": token["address"],
        "odos_price_usdt": odos if isinstance(odos, float) else None,
        "mexc_price_usdt": mexc if isinstance(mexc, float) else None,
        "error": None if isinstance(odos, float) and isinstance(mexc, float) else f"{odos if not isinstance(odos,float) else ''} {mexc if not isinstance(mexc,float) else ''}".strip()
    }

def get_all_prices():
    """Возвращает кэшированные цены, обновляя при необходимости"""
    global LAST_UPDATE
    if time.time() - LAST_UPDATE > CACHE_TTL:
        asyncio.run(update_prices())
    return PRICE_CACHE
