# PolygonScan.py
from fastapi import APIRouter
import requests
import time
from datetime import datetime
from web3 import Web3

router = APIRouter()

# API и адреса
API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
SUT_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"
ADDRESS = SUT_CONTRACT  # Считаем транзакции самого токена
POLYGON_RPC = "https://polygon-rpc.com"
MEXC_API_PRICE = "https://www.mexc.com/open/api/v2/market/ticker?symbol=SUT_USDT"

# Web3 для total supply
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
ABI = [{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
contract = w3.eth.contract(address=SUT_CONTRACT, abi=ABI)

@router.get("/polygonscan/data")
def get_sut_transactions():
    try:
        # --- Получаем транзакции токена ---
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid=137&module=account&action=tokentx"
            f"&address={ADDRESS}&sort=desc&apikey={API_KEY}"
        )
        resp = requests.get(url, timeout=10).json()
        txs = resp.get("result", [])
        now = int(time.time())
        one_hour_ago = now - 3600

        total_sut = 0
        sut_txs = []

        for tx in txs:
            if tx["contractAddress"].lower() == SUT_CONTRACT.lower():
                ts = int(tx["timeStamp"])
                if ts >= one_hour_ago:
                    value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
                    total_sut += value
                    sut_txs.append({
                        "hash": tx["hash"],
                        "from": tx["from"],
                        "to": tx["to"],
                        "value": value,
                        "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    })

        # --- Получаем цену токена с MEXC ---
        price_usdt = 0.0
        try:
            price_resp = requests.get(MEXC_API_PRICE, timeout=10).json()
            price_usdt = float(price_resp['data'][0]['lastPrice'])
        except:
            price_usdt = 0.0

        # --- Total Supply через Web3 ---
        total_supply = contract.functions.totalSupply().call() / (10**18)

        # --- Рассчёт % от supply и капитализации ---
        percent_of_supply = (total_sut / total_supply * 100) if total_supply > 0 else 0
        market_cap = total_supply * price_usdt

        total_usdt = total_sut * price_usdt

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
        return {"error": str(e), "total_sut": 0, "total_usdt":0, "price_usdt":0, "total_supply":0,
                "percent_of_supply":0, "market_cap":0, "transactions":[]}
