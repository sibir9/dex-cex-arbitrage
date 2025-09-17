# PolygonScan.py
from fastapi import APIRouter
import requests
import time
from datetime import datetime

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
ADDRESS = "0x6cc2b9092a8a46fb8e07b2649d6d8f4845e94e4b"
SUT_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"

@router.get("/Polygonscan/data")
def get_sut_transactions():
    url = (
        "https://api.etherscan.io/v2/api"
        f"?chainid=137&module=account&action=tokentx"
        f"&address={ADDRESS}&sort=desc&apikey={API_KEY}"
    )
    resp = requests.get(url).json()
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

    return {"total_sut": total_sut, "transactions": sut_txs}
