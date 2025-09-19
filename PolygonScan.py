from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests, time, json
from datetime import datetime
from pathlib import Path
from web3 import Web3

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"

# Загружаем список токенов
TOKENS_FILE = Path(__file__).parent / "poltokens.json"
with open(TOKENS_FILE, "r") as f:
    TOKENS = json.load(f)

# Web3
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# ABI минимальный для totalSupply и decimals
ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

def get_price(symbol: str) -> float:
    """Берем цену токена в USDT с MEXC"""
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        resp = requests.get(url, params={"symbol": symbol}, timeout=10).json()
        price = resp.get("price")
        if price is None:
            raise ValueError("price not in response")
        return float(price)
    except Exception as e:
        print(f"Error fetching {symbol} price from MEXC:", e)
        return 0.0

def get_total_supply(contract_address: str) -> float:
    """Берем totalSupply токена через Web3"""
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=ABI)
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        return total_supply
    except Exception as e:
        print(f"Error fetching total supply for {contract_address}:", e)
        return 0.0

@router.get("/Polygonscan/data")
def polygonscan_data():
    result = {}
    now = int(time.time())
    one_hour_ago = now - 3600

    for token, info in TOKENS.items():
        try:
            contract_address = info["contract"]
            symbol = info["symbol"]

            # цена и supply
            price_usdt = get_price(symbol)
            total_supply = get_total_supply(contract_address)

            # Транзакции за час
            url = (
                "https://api.etherscan.io/v2/api"
                f"?chainid=137&module=account&action=tokentx"
                f"&contractaddress={contract_address}&sort=desc&apikey={API_KEY}"
            )
            resp = requests.get(url, timeout=10).json()
            txs = resp.get("result", [])

            total_amount = 0.0
            tx_list = []
            for tx in txs:
                ts = int(tx.get("timeStamp", 0))
                if ts >= one_hour_ago:
                    value_raw = int(tx.get("value", 0))
                    token_decimal = int(tx.get("tokenDecimal", 18))
                    value = value_raw / (10 ** token_decimal)
                    total_amount += value
                    tx_list.append({
                        "hash": tx.get("hash"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "value": value,
                        "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    })

            total_usdt = total_amount * price_usdt
            percent_of_supply = (total_amount / total_supply * 100) if total_supply > 0 else 0.0
            market_cap = total_supply * price_usdt

            result[token] = {
                "price_usdt": price_usdt,
                "total": total_amount,
                "total_usdt": total_usdt,
                "percent_of_supply": percent_of_supply,
                "market_cap": market_cap,
                "transactions": tx_list
            }
        except Exception as e:
            result[token] = {
                "error": str(e),
                "price_usdt": 0.0,
                "total": 0.0,
                "total_usdt": 0.0,
                "percent_of_supply": 0.0,
                "market_cap": 0.0,
                "transactions": []
            }

    return JSONResponse(result)
