import requests

CHAIN_ID = 137  # Polygon
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"  # USDT (Polygon)
ODOS_FEE = 0.002  # 0.2%
MEXC_FEE = 0.001  # 0.1%

TOKENS = [
    {"symbol": "NAKA", "address": "0x311434160d7537be358930def317afb606c0d737"},
    {"symbol": "SAND", "address": "0xbbba073c31bf03b8acf7c28ef0738decf3695683"},
    {"symbol": "ZRO", "address": "0x6985884c4392d348587b19cb9eaaf157f13271cd"},
    {"symbol": "MV", "address": "0xa3c322ad15218fbfaed26ba7f616249f7705d945"},
    {"symbol": "UPO", "address": "0x9dbfc1cbf7a1e711503a29b4b5f9130ebeccac96"},
    {"symbol": "QUICK", "address": "0xb5c064f955d8e7f38fe0460c556a72987494ee17"},
    {"symbol": "COCA", "address": "0x7b12598e3616261df1c05ec28de0d2fb10c1f206"},
    {"symbol": "NWS", "address": "0x13646e0e2d768d31b75d1a1e375e3e17f18567f2"},
]

def get_all_prices():
    result = {}
    for token in TOKENS:
        res = {"odos_price_usdt": None, "mexc_price_usdt": None, "error": None}
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
            depth_resp = requests.get(f"https://api.mexc.com/api/v3/depth?symbol={token['symbol']}USDT&limit=50", timeout=10).json()
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
        except Exception as e:
            res["error"] = str(e)
        result[token["symbol"]] = res
    return result
# version 4
