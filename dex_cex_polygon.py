import requests

CHAIN_ID = 137  # Polygon
USDT = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"  # USDT (Polygon)
ODOS_FEE = 0.002  # 0.2%
MEXC_FEE = 0.001  # 0.1%

TOKENS = [
    {"symbol": "NAKA", "address": "0x311434160d7537be358930def317afb606c0d737"},
    {"symbol": "SAND", "address": "0xbbba073c31bf03b8acf7c28ef0738decf3695683"},
    {"symbol": "ZRO", "address": "0x6985884c4392d348587b19cb9eaaf157f13271cd"},
    {"symbol": "COCA", "address": "0x7b12598e3616261df1c05ec28de0d2fb10c1f206"},
    {"symbol": "NWS", "address": "0x13646e0e2d768d31b75d1a1e375e3e17f18567f2"},
    {"symbol": "MV", "address": "0xa3c322ad15218fbfaed26ba7f616249f7705d945"},
    {"symbol": "UPO", "address": "0x9dbfc1cbf7a1e711503a29b4b5f9130ebeccac96"},
    {"symbol": "QUICK", "address": "0xb5c064f955d8e7f38fe0460c556a72987494ee17"},
    {"symbol": "APEPE", "address": "0xa3f751662e282e83ec3cbc387d225ca56dd63d3a"},
    {"symbol": "SUT", "address": "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"},
    {"symbol": "VCNT", "address": "0x8a16d4bf8a0a716017e8d2262c4ac32927797a2f"},
    {"symbol": "GNS", "address": "0xe5417af564e4bfda1c483642db72007871397896"},
    {"symbol": "GEOD", "address": "0xac0f66379a6d7801d7726d5a943356a172549adb"},
    {"symbol": "MLC", "address": "0x0566c506477cd2d8df4e0123512dbc344bd9d111"},
    {"symbol": "EMT", "address": "0x708383ae0e80e75377d664e4d6344404dede119a"},
    {"symbol": "IXT", "address": "0xe06bd4f5aac8d0aa337d13ec88db6defc6eaeefe"},
    {"symbol": "VOXEL", "address": "0xd0258a3fd00f38aa8090dfee343f10a9d4d30d3f"},
    {"symbol": "KASTA", "address": "0x235737dbb56e8517391473f7c964db31fa6ef280"},
    {"symbol": "SOIL", "address": "0x43c73b90e0c2a355784dcf0da12f477729b31e77"},
    {"symbol": "MPT", "address": "0x87d6f8edeccbcca766d2880d19b2c3777d322c22"},
    {"symbol": "SWCH", "address": "0x3ce1327867077b551ae9a6987bf10c9fd08edce1"},
    {"symbol": "UBU", "address": "0x78445485a8d5b3be765e3027bc336e3c272a23c9"},
    {"symbol": "XPED", "address": "0x8689aedf32d35aa9a90849f59ba6841c389e6cf9"},
    {"symbol": "RAIN", "address": "0x8e677ca17065ed74675bc27bcabadb7eef10a292"},
    {"symbol": "NRS", "address": "0x94615302bcb36309371ea7454f3e99a4002105de"},
    {"symbol": "FURI", "address": "0x5742fe477b2afed92c25d092418bac06cd076cea"},
    {"symbol": "ECET", "address": "0xc1ab7e48fafee6b2596c65261392e59690ce7742"},
    {"symbol": "BB", "address": "0x4f7cc8ef14f3dc76ee2fb60028749e1b61cea162"},
    {"symbol": "PolyDoge", "address": "0x8a953cfe442c5e8855cc6c61b1293fa648bae472"},
    {"symbol": "AKI", "address": "0x1a7e49125a6595588c9556f07a4c006461b24545"},
    {"symbol": "IBS", "address": "0xb9df5fda1c435cd4017a1f1f9111996520b64439"},
    {"symbol": "CARR", "address": "0x9b765735c82bb00085e9dbf194f20e3fa754258e"},
    {"symbol": "DEOD", "address": "0xe77abb1e75d2913b2076dd16049992ffeaca5235"},
    {"symbol": "ASK", "address": "0xaa3717090cddc9b227e49d0d84a28ac0a996e6ff"},
    {"symbol": "WIFI", "address": "0xe238ecb42c424e877652ad82d8a939183a04c35f"},
    {"symbol": "WPAY", "address": "0x7abe9edf5c544a04da83e9110cf46dbc4759170c"},
    {"symbol": "UDAO", "address": "0x433ccebc95ad458e74d81837db0d4aa27e30e117"},
    {"symbol": "DTEC", "address": "0xd87af7b418d64ff2cde48d890285ba64fc6e115f"},
    {"symbol": "VDA", "address": "0x683565196c3eab450003c964d4bad1fd3068d4cc"},
    {"symbol": "EDX", "address": "0xc114678c6e4654d041b2006c90f08478b444c4e2"},
    {"symbol": "W3GG", "address": "0x8d60fb5886497851aac8c5195006ecf07647ba0d"},
    {"symbol": "MINX", "address": "0x552f4d98f338fbbd3175ddf38ce1260f403bbba2"},
    {"symbol": "VATRENI", "address": "0xd60deba014459f07bbcc077a5b817f31dafd5229"},
    {"symbol": "WEFI", "address": "0xffa188493c15dfaf2c206c97d8633377847b6a52"},
    {"symbol": "WSDM", "address": "0x5f2f8818002dc64753daedf4a6cb2ccb757cd220"},
    {"symbol": "TEL", "address": "0xdf7837de1f2fa4631d716cf2502f8b230f1dcc32"},
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
