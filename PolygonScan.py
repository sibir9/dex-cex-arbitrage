from fastapi import APIRouter
import requests
import time
from datetime import datetime

router = APIRouter()

API_KEY = "P1WGRYNN24JQQGR6EH9PWWDRJQWQVBR9AK"
TOKEN_CONTRACT = "0x98965474ecbec2f532f1f780ee37b0b05f77ca55"  # SUT

# 🔹 Известные CEX кошельки (минимальный набор)
CEX_WALLETS = {
    "Binance": {
        "0x3f5CE5FBFe3E9af3971dD833D26BA9b5C936f0bE".lower(),  # основной
        "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245".lower(),  # Binance 48 (обнаружен на PolygonScan)
    },
    "KuCoin": {
        "0x2a0c0debf3b94f7e5f31352c71f9f76b9c7e4a97".lower(),
    },
    "OKX": {
        "0x2c8C3b8dCeA2f44eE1A91b3E5d7fC84e5aE3D4b2".lower(),
    },
    "MEXC": {
        "0x9f84a01b05e1f5f5f946a07a83bdb0666ec07c6d".lower(),
        "0x51e3d44172868acc60d68ca99591ce4230bc75e0".lower(),  # адрес с меткой MEXC
        "0x2e8f79ad740de90dc5f5a9f0d8d9661a60725e64".lower(),  # “MEXC 5”
    },
    "Bybit": {
        "0x9f7fc5f7c0b2d3b4b3a26e9e22a7c6b2c72e63b5".lower(),
    }
}


def detect_cex(address: str) -> str:
    """Определяем, принадлежит ли адрес CEX"""
    addr = address.lower()
    for cex, wallets in CEX_WALLETS.items():
        if addr in wallets:
            return cex
    return "User"


@router.get("/polygonscan/data")
def get_sut_transactions():
    try:
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid=137&module=account&action=tokentx"
            f"&address={TOKEN_CONTRACT}&sort=desc&apikey={API_KEY}"
        )
        resp = requests.get(url, timeout=10).json()
        txs = resp.get("result", [])
        now = int(time.time())
        one_hour_ago = now - 3600

        total_sut = 0
        sut_txs = []

        for tx in txs:
            if tx["contractAddress"].lower() == TOKEN_CONTRACT.lower():
                ts = int(tx["timeStamp"])
                if ts >= one_hour_ago:
                    value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
                    total_sut += value
                    sut_txs.append({
                        "hash": tx["hash"],
                        "from": tx["from"],
                        "to": tx["to"],
                        "value": value,
                        "time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        "cex": detect_cex(tx["to"])
                    })

        return {"total_sut": total_sut, "transactions": sut_txs}

    except Exception as e:
        return {"error": str(e), "total_sut": 0, "transactions": []}
