from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests, time
from datetime import datetime
from web3 import Web3

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
SUT_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"

def get_sut_price():
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        params = {"symbol": "SUTUSDT"}
        resp = requests.get(url, params=params, timeout=10).json()
        price = resp.get("price")
        if price is None:
            raise ValueError("price not in response")
        return float(price)
    except Exception as e:
        print("Error fetching SUT price from MEXC:", e)
        return 0.0




# Web3
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
SUT_CONTRACT_RAW = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"
SUT_CONTRACT = Web3.to_checksum_address(SUT_CONTRACT_RAW)

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

contract = w3.eth.contract(address=SUT_CONTRACT, abi=ABI)

def get_total_supply():
    try:
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        return total_supply
    except Exception as e:
        print("Error fetching total supply via Web3:", e)
        return 0.0







@router.get("/Polygonscan/data")
def polygonscan_data():
    try:
        price_usdt = get_sut_price()
        total_supply = get_total_supply()

        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid=137&module=account&action=tokentx"
            f"&contractaddress={SUT_CONTRACT}&sort=desc&apikey={API_KEY}"
        )
        resp = requests.get(url, timeout=10).json()
        txs = resp.get("result", [])

        now = int(time.time())
        one_hour_ago = now - 3600

        total_sut = 0.0
        sut_txs = []

        for tx in txs:
            ts = int(tx.get("timeStamp", 0))
            if ts >= one_hour_ago:
                value_raw = int(tx.get("value", 0))
                token_decimal = int(tx.get("tokenDecimal", 18))
                value = value_raw / (10 ** token_decimal)
                total_sut += value
                sut_txs.append({
                    "hash": tx.get("hash"),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "value": value,
                    "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                })

        total_usdt = total_sut * price_usdt
        percent_of_supply = (total_sut / total_supply * 100) if total_supply > 0 else 0.0
        market_cap = total_supply * price_usdt

        return JSONResponse({
            "price_usdt": price_usdt,
            "total_sut": total_sut,
            "total_usdt": total_usdt,
            "percent_of_supply": percent_of_supply,
            "market_cap": market_cap,
            "transactions": sut_txs
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "price_usdt": 0.0,
            "total_sut": 0.0,
            "total_usdt": 0.0,
            "percent_of_supply": 0.0,
            "market_cap": 0.0,
            "transactions": []
        })
