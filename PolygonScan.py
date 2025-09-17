from fastapi import APIRouter
import requests
import time
from datetime import datetime

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
ADDRESS = "0x6cc2b9092a8a46fb8e07b2649d6d8f4845e94e4b"
SUT_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"

ETHERSCAN_API = "https://api.etherscan.io/v2/api"
MEXC_API = "https://api.mexc.com/api/v3/ticker/price?symbol=SUTUSDT"


def get_mexc_price():
    try:
        res = requests.get(MEXC_API, timeout=10).json()
        return float(res.get("price", 0))
    except Exception:
        return 0


def get_total_supply():
    try:
        url = (
            f"{ETHERSCAN_API}?chainid=137&module=token&action=tokeninfo"
            f"&contractaddress={SUT_CONTRACT}&apikey={API_KEY}"
        )
        res = requests.get(url, timeout=10).json()
        if "result" in res and isinstance(res["result"], list):
            supply_raw = int(res["result"][0].get("totalSupply", 0))
            decimals = int(res["result"][0].get("decimals", 18))
            return supply_raw / (10 ** decimals)
    except Exception:
        pass
    return 0


@router.get("/Polygonscan/data")
def get_sut_transactions():
    try:
        # Получаем все транзакции токена
        url = (
            f"{ETHERSCAN_API}?chainid=137&module=account&action=tokentx"
            f"&address={SUT_CONTRACT}&sort=desc&apikey={API_KEY}"
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

        # Берём цену с MEXC
        price = get_mexc_price()

        # Total Supply
        total_supply = get_total_supply()

        # Расчёты
        total_usdt = total_sut * price
        percent_of_supply = (total_sut / total_supply * 100) if total_supply > 0 else 0
        market_cap = total_supply * price if total_supply > 0 else 0

        return {
            "total_sut": total_sut,
            "total_usdt": total_usdt,
            "price_usdt": price,
            "total_supply": total_supply,
            "percent_of_supply": percent_of_supply,
            "market_cap": market_cap,
            "transactions": sut_txs
        }

    except Exception as e:
        return {"error": str(e), "total_sut": 0, "transactions": []}
