from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests, time, json, os
from datetime import datetime
from web3 import Web3

router = APIRouter()

API_KEY = "ТВОЙ_API_KEY"  # ключ Etherscan
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# ABI минимальный
ABI = [
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

# Загружаем список токенов
TOKENS_FILE = "poltokens.json"
if not os.path.exists(TOKENS_FILE):
    raise FileNotFoundError("Файл poltokens.json не найден")
with open(TOKENS_FILE) as f:
    TOKENS = json.load(f)

def get_price_usdt(pair: str):
    """Цена токена с MEXC"""
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        params = {"symbol": pair}
        resp = requests.get(url, params=params, timeout=10).json()
        return float(resp.get("price", 0))
    except Exception as e:
        print(f"Error fetching {pair} price from MEXC:", e)
        return 0.0

def get_total_supply(address: str):
    """Total supply через Web3"""
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ABI)
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        return total_supply
    except Exception as e:
        print(f"Error fetching total supply for {address}:", e)
        return 0.0


@router.get("/polygonscan/data")
def polygonscan_data():
    try:
        results = {}
        now = int(time.time())
        one_hour_ago = now - 3600

        for token in TOKENS:
            symbol = token["symbol"]
            address = token["address"]
            pair = token.get("pair", f"{symbol}USDT")

            # 1. Цена
            price_usdt = get_price_usdt(pair)

            # 2. Total supply
            total_supply = get_total_supply(address)

            # 3. Транзакции
            url = (
                "https://api.etherscan.io/v2/api"
                f"?chainid=137&module=account&action=tokentx"
                f"&contractaddress={address}&sort=desc&apikey={API_KEY}"
            )
            resp = requests.get(url, timeout=10).json()
            if resp.get("status") != "1" or "result" not in resp:
                print(f"No tx data for {symbol}: {resp.get('message')}")
                txs = []
            else:
                txs = resp["result"]

            total_amount = 0.0
            token_txs = []

            for tx in txs:
                ts = int(tx.get("timeStamp", 0))
                if ts >= one_hour_ago:
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

            # 4. Финальные метрики
            total_usdt = total_amount * price_usdt
            percent_of_supply = (total_amount / total_supply * 100) if total_supply > 0 else 0.0
            market_cap = total_supply * price_usdt if total_supply > 0 else 0.0

            results[symbol] = {
                "symbol": symbol,
                "address": address,
                "price_usdt": price_usdt,
                "total_transferred": total_amount,
                "total_usdt": total_usdt,
                "percent_of_supply": percent_of_supply,
                "market_cap": market_cap,
                "transactions": token_txs
            }

        return JSONResponse(results)

    except Exception as e:
        return JSONResponse({"error": str(e)})
