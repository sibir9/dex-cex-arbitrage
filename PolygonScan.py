from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests, time, json, os, asyncio
from datetime import datetime
from web3 import Web3

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"  # Etherscan API
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

ABI = [
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

TOKENS_FILE = "poltokens.json"
if not os.path.exists(TOKENS_FILE):
    raise FileNotFoundError("Файл poltokens.json не найден")
with open(TOKENS_FILE) as f:
    TOKENS = json.load(f)

# ================= КЭШ =================
DATA_CACHE = {}
SUPPLY_CACHE = {}

# ================= HELPERS =================
def get_price_usdt(pair: str):
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        params = {"symbol": pair}
        resp = requests.get(url, params=params, timeout=10).json()
        return float(resp.get("price", 0))
    except Exception as e:
        print(f"Error fetching {pair} price:", e)
        return 0.0


def get_total_supply(address: str):
    if address in SUPPLY_CACHE:  # кэшируем supply/decimals
        return SUPPLY_CACHE[address]

    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ABI)
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        SUPPLY_CACHE[address] = total_supply
        return total_supply
    except Exception as e:
        print(f"Error fetching total supply for {address}:", e)
        return 0.0


def collect_token_data(symbol: str, address: str, pair: str):
    now = int(time.time())
    thirty_minutes_ago = now - 1800

    # Цена
    price_usdt = get_price_usdt(pair)

    # Total supply
    total_supply = get_total_supply(address)

    # Транзакции
    url = (
        "https://api.etherscan.io/v2/api"
        f"?chainid=137&module=account&action=tokentx"
        f"&contractaddress={address}&starttimestamp={thirty_minutes_ago}"
        f"&sort=desc&apikey={API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=10).json()
        txs = resp.get("result", []) if resp.get("status") == "1" else []
    except Exception as e:
        print(f"Error fetching txs for {symbol}:", e)
        txs = []

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

# ================= BACKGROUND REFRESH =================
async def refresh_data():
    while True:
        results = {}
        for token in TOKENS:
            try:
                results[token["symbol"]] = collect_token_data(
                    token["symbol"], token["address"], token.get("pair", f'{token["symbol"]}USDT')
                )
            except Exception as e:
                results[token["symbol"]] = {"error": str(e)}
        global DATA_CACHE
        DATA_CACHE = results
        await asyncio.sleep(30)  # обновляем каждые 30 секунд

@router.on_event("startup")
async def startup_event():
    asyncio.create_task(refresh_data())

# ================= ENDPOINTS =================
@router.get("/polygonscan/data")
def polygonscan_data():
    return JSONResponse(DATA_CACHE or {"error": "Cache is empty, please wait a few seconds"})

@router.get("/polygonscan/summary")
def polygonscan_summary():
    if not DATA_CACHE:
        return JSONResponse({"error": "Cache is empty, please wait a few seconds"})
    summary = []
    for token, data in DATA_CACHE.items():
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
