import requests
import json
import os

CHAIN_ID = 137  # Polygon
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"
ODOS_FEE = 0.002
MEXC_FEE = 0.001
QUICKSWAP_FEE = 0.002  # 0.2%

# Загружаем список токенов из JSON
TOKENS_FILE = os.path.join(os.path.dirname(__file__), "poltokens.json")
with open(TOKENS_FILE, "r") as f:
    TOKENS = json.load(f)

QUICKSWAP_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/ianlapham/quickswap"

def get_quickswap_price(token_address):
    """
    Возвращает цену токена в USDT на QuickSwap через TheGraph с учетом комиссии.
    """
    token_address = token_address.lower()
    usdt_address = USDT.lower()
    query = """
    {{
      pairs(first: 1, where: {{token0_in: ["{token}", "{usdt}"], token1_in: ["{token}", "{usdt}"]}}) {{
        token0 {{ id }}
        token1 {{ id }}
        token0Price
        token1Price
      }}
    }}
    """.format(token=token_address, usdt=usdt_address)

    resp = requests.post(QUICKSWAP_SUBGRAPH, json={"query": query}, timeout=10).json()
    pairs = resp.get("data", {}).get("pairs")
    if not pairs:
        return None

    pair = pairs[0]
    token0 = pair["token0"]["id"].lower()
    token1 = pair["token1"]["id"].lower()

    if token0 == token_address and token1 == usdt_address:
        price = float(pair["token1Price"])
    elif token1 == token_address and token0 == usdt_address:
        price = float(pair["token0Price"])
    else:
        return None

    # Учитываем комиссию QuickSwap
    return price * (1 + QUICKSWAP_FEE)

def get_all_prices():
    result = {}
    for token in TOKENS:
        res = {
            "odos_price_usdt": None,
            "mexc_price_usdt": None,
            "quickswap_price_usdt": None,
            "error": None
        }
        try:
            # === ODOS ===
            effective_usdt = 50 * (1 - ODOS_FEE)
            odos_resp = requests.post(
                "https://api.odos.xyz/sor/quote/v2",
                json={
                    "chainId": CHAIN_ID,
                    "inputTokens": [{"tokenAddress": USDT, "amount": str(int(effective_usdt * 1e6))}],
                    "outputTokens": [{"tokenAddress": token["address"]}],
                    "slippageLimitPercent": 1
                },
                timeout=10
            ).json()
            out_amount = odos_resp.get("outAmounts", [None])[0]
            if out_amount:
                tokens_bought = int(out_amount) / 1e18
                res["odos_price_usdt"] = effective_usdt / tokens_bought

            # === MEXC ===
            depth_resp = requests.get(
                f"https://api.mexc.com/api/v3/depth?symbol={token['symbol']}USDT&limit=50",
                timeout=10
            ).json()
            bids = depth_resp.get("bids", [])
            if bids and out_amount:
                remaining_tokens = tokens_bought
                total_usdt = 0
                for price_str, qty_str in bids:
                    price = float(price_str)
                    qty = float(qty_str)
                    if remaining_tokens >= qty:
                        total_usdt += price * qty
                        remaining_tokens -= qty
                    else:
                        total_usdt += price * remaining_tokens
                        remaining_tokens = 0
                        break
                if remaining_tokens == 0:
                    res["mexc_price_usdt"] = total_usdt / tokens_bought

            # === QuickSwap ===
            try:
                res["quickswap_price_usdt"] = get_quickswap_price(token["address"])
            except Exception as e:
                res["error"] = f"QuickSwap error: {str(e)}"

        except Exception as e:
            res["error"] = str(e)

        result[token["symbol"]] = res

    return result

# version 5
