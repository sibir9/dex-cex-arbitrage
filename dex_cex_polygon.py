import requests
import json
import os

CHAIN_ID = 137  # Polygon
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"
ODOS_FEE = 0.002
MEXC_FEE = 0.001
QUICKSWAP_FEE = 0.002

# Загружаем токены из JSON
TOKENS_FILE = os.path.join(os.path.dirname(__file__), "poltokens.json")
with open(TOKENS_FILE, "r") as f:
    TOKENS = json.load(f)

QUICKSWAP_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/ianlapham/quickswap"

def get_quickswap_price(token_address: str) -> float | None:
    """Возвращает цену токена в USDT на QuickSwap через новый subgraph"""
    token_address = token_address.lower()
    query = """
    query {
      token(id: "%s") {
        derivedETH
      }
      bundle(id: "1") {
        ethPrice
      }
    }
    """ % token_address

    try:
        resp = requests.post(QUICKSWAP_SUBGRAPH, json={"query": query}, timeout=10).json()
        token_data = resp.get("data", {}).get("token")
        bundle_data = resp.get("data", {}).get("bundle")

        if not token_data or not bundle_data:
            return None

        derived_eth = float(token_data["derivedETH"])
        eth_price_usd = float(bundle_data["ethPrice"])
        price_usdt = derived_eth * eth_price_usd

        # Учитываем комиссию QuickSwap
        price_usdt *= (1 + QUICKSWAP_FEE)
        return price_usdt

    except Exception as e:
        print(f"QuickSwap error: {e}")
        return None

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

# version 6
