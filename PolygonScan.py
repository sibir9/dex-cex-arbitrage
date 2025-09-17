# PolygonScan.py
from fastapi import APIRouter
import requests
import time
from datetime import datetime
from web3 import Web3

router = APIRouter()

# Настройки
API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
SUT_CONTRACT_RAW = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"

# Web3
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
SUT_CONTRACT = Web3.to_checksum_address(SUT_CONTRACT_RAW)

# ABI токена (минимально необходимое для totalSupply и decimals)
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

contract = w3.eth.contract(address=SUT_CONTRACT, abi=ABI)

# CEX адреса (пример)
CEX_ADDRESSES = {
    "Binance": ["0x..."],  # добавь реальные адреса
    "Bybit": ["0x..."],
    "MEXC": ["0x..."]
}

# Получение цены SUT в USDT с MEXC
def get_price_usdt():
    try:
        url = "https://www.mexc.com/api/v3/ticker/price?symbol=SUTUSDT"
        resp = requests.get(url, timeout=5).json()
        return float(resp["price"])
    except Exception:
        return 0.0

@router.get("/polygonscan/data")
def get_sut_transactions():
    try:
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid=137&module=account&action=tokentx"
            f"&address={SUT_CONTRACT}&sort=desc&apikey={API_KEY}"
        )
        resp = requests.get(url, timeout=10).json()
        txs = resp.get("result", [])
        now = int(time.time())
        one_hour_ago = now - 3600

        total_sut = 0
        sut_txs = []

        for tx in txs:
            if tx["contractAddress"].lower() == SUT_CONTRACT_RAW.lower():
                ts = int(tx["timeStamp"])
                if ts >= one_hour_ago:
                    value = int(tx["value"]) / (10 ** contract.functions.decimals().call())
                    total_sut += value
                    is_cex = any(tx["to"].lower() in [addr.lower() for addrs in CEX_ADDRESSES.values() for addr in addrs])
                    sut_txs.append({
                        "hash": tx["hash"],
                        "from": tx["from"],
                        "to": tx["to"],
                        "value": value,
                        "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        "cex": is_cex
                    })

        price_usdt = get_price_usdt()
        total_usdt = total_sut * price_usdt

        total_supply = contract.functions.totalSupply().call() / (10 ** contract.functions.decimals().call())
        percent_of_supply = (total_sut / total_supply * 100) if total_supply else 0
        market_cap = total_supply * price_usdt if total_supply else 0

        return {
            "total_sut": total_sut,
            "total_usdt": total_usdt,
            "price_usdt": price_usdt,
            "total_supply": total_supply,
            "percent_of_supply": percent_of_supply,
            "market_cap": market_cap,
            "transactions": sut_txs
        }

    except Exception as e:
        return {"error": str(e), "total_sut": 0, "total_usdt": 0.0, "price_usdt": 0.0,
                "total_supply": 0, "percent_of_supply": 0, "market_cap": 0, "transactions": []}
