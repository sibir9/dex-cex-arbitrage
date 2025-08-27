#!/bin/bash
cd /root/dex-cex-arbitrage || exit
git reset --hard
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart fastapi.service
