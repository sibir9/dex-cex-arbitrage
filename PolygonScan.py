from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests, time, json, os
from datetime import datetime
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor, as_completed

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

ABI = [
    {"constant": True, "inputs": [], "name": "totalSupply",
     "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

TOKENS_FILE = "poltokens.json"
if not os.path.exists(TOKENS_FILE):
    raise FileNotFoundError("Файл poltokens.json не найден")
with open(TOKENS_FILE) as f:
    TOKENS = json.load(f)

CACHE = {}
CACHE_TIMESTAMP = 0
CACHE_TTL = 60  # кэш живёт 1 минуту


def get_price_usdt(pair: str):
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        resp = requests.get(url, params={"symbol": pair}, timeout=5).json()
        return float(resp.get("price", 0))
    except Exception as e:
        print(f"Error fetching {pair} price:", e)
        return 0.0


def get_total_supply(address: str):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ABI)
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        return total_supply
    except Exception as e:
        print(f"Error fetching total supply for {address}:", e)
        return 0.0


def collect_token_data(symbol: str, address: str, pair: str):
    now = int(time.time())
    thirty_min_ago = now - 1800  # последние 30 минут

    # Цена
    price_usdt = get_price_usdt(pair)

    # Total supply
    total_supply = get_total_supply(address)

    # Транзакции
    url = (
        "https://api.etherscan.io/v2/api"
        f"?chainid=137&module=account&action=tokentx"
        f"&contractaddress={address}&starttimestamp={thirty_min_ago}"
        f"&endtimestamp={now}&sort=desc&apikey={API_KEY}"
    )

    try:
        resp = requests.get(url, timeout=5).json()
    except Exception as e:
        return {"symbol": symbol, "error": f"tx fetch error: {e}"}

    if resp.get("status") != "1" or "result" not in resp:
        return {"symbol": symbol, "error": resp.get("message", "no result")}

    txs = resp["result"]

    total_amount = 0.0
    token_txs = []

    for tx in txs:
        ts = int(tx.get("timeStamp", 0))
        value_raw = int(tx.get("value", 0))
        decimals = int(tx.get("tokenDecimal", 18))
        value = value_raw / (10 ** decimals)
        total_amount += value
        token_txs.append({
            "hash": tx.get("hash"),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value": value,
            "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        })

    total_usdt = total_amount * price_usdt
    percent_of_supply = (total_amount / total_supply * 100) if total_supply > 0 else 0.0
    market_cap = total_supply * price_usdt if total_supply > 0 else 0.0

    return {
        "symbol": symbol,
        "address": address,
        "price_usdt": price_usdt,
        "total_transferred": total_amount,
        "total_usdt": total_usdt,
        "percent_of_supply": percent_of_supply,
        "market_cap": market_cap,
        "transactions": token_txs
    }


def refresh_cache():
    global CACHE, CACHE_TIMESTAMP
    print("Refreshing cache...")

    results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_token = {
            executor.submit(
                collect_token_data,
                token["symbol"],
                token["address"],
                token.get("pair", f'{token["symbol"]}USDT')
            ): token for token in TOKENS
        }

        for future in as_completed(future_to_token):
            token = future_to_token[future]
            try:
                results[token["symbol"]] = future.result()
            except Exception as e:
                print(f"Token {token['symbol']} failed: {e}")
                results[token["symbol"]] = {"error": str(e)}

    CACHE = results
    CACHE_TIMESTAMP = int(time.time())
    print("Cache updated")


def get_cache():
    global CACHE_TIMESTAMP
    now = int(time.time())
    if now - CACHE_TIMESTAMP > CACHE_TTL or not CACHE:
        refresh_cache()
    return CACHE


@router.get("/polygonscan/data")
def polygonscan_data():
    return JSONResponse(get_cache())


@router.get("/polygonscan/summary")
def polygonscan_summary():
    cache = get_cache()
    summary = []
    for symbol, data in cache.items():
        if "error" in data:
            continue
        summary.append({
            "symbol": data["symbol"],
            "price_usdt": data["price_usdt"],
            "total_transferred": data["total_transferred"],
            "total_usdt": data["total_usdt"],
            "percent_of_supply": data["percent_of_supply"],
            "market_cap": data["market_cap"]
        })
    return JSONResponse(summary)
