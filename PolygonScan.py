from fastapi import APIRouter
import requests
import time
from datetime import datetime

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
SUT_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"

@router.get("/polygonscan/data")
def get_sut_transactions():
    try:
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid=137&module=account&action=tokentx"
            f"&contractaddress={SUT_CONTRACT}&sort=desc&apikey={API_KEY}"
        )
        resp = requests.get(url, timeout=10)
        print("Etherscan response:", resp.text)  # Логируем для отладки
        txs = resp.json().get("result", [])

        now = int(time.time())
        one_hour_ago = now - 3600

        total_sut = 0
        sut_txs = []

        for tx in txs:
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

        return {"total_sut": total_sut, "transactions": sut_txs}

    except Exception as e:
        return {"error": str(e), "total_sut": 0, "transactions": []}
