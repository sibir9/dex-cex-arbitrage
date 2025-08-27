#!/bin/bash

# Переходим в корень проекта
cd /root/dex-cex-arbitrage || exit

# Логируем процесс
echo "===== Deploy started at $(date) =====" >> deploy.log

# Сбрасываем изменения и подтягиваем ветку main
git reset --hard >> deploy.log 2>&1
git pull origin main >> deploy.log 2>&1

# Обновляем зависимости (если нужны)
source venv/bin/activate
pip install -r requirements.txt >> deploy.log 2>&1

# Перезапускаем FastAPI сервис
systemctl restart fastapi.service >> deploy.log 2>&1

echo "===== Deploy finished at $(date) =====" >> deploy.log
