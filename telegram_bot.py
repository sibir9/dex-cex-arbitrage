import os
import asyncio
import sqlite3
import aiohttp
from cryptography.fernet import Fernet
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем .env_bot
load_dotenv(".env_bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FERNET_KEY = os.getenv("FERNET_KEY")

if BOT_TOKEN is None or FERNET_KEY is None:
    raise RuntimeError("Не найдены TELEGRAM_BOT_TOKEN или FERNET_KEY в .env_bot")

fernet = Fernet(FERNET_KEY.encode())

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Работа с SQLite ---
DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_hash TEXT UNIQUE,
            min_spread REAL DEFAULT 0.5
        )
    """)
    conn.commit()
    conn.close()

def add_user(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    chat_hash = fernet.encrypt(str(chat_id).encode()).decode()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users (chat_hash, min_spread) VALUES (?, ?)
        """, (chat_hash, 0.5))
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_hash, min_spread FROM users")
    rows = cursor.fetchall()
    conn.close()
    users = []
    for row in rows:
        try:
            chat_id = int(fernet.decrypt(row[0].encode()).decode())
            users.append((chat_id, row[1]))
        except Exception:
            continue
    return users

def update_user_spread(chat_id: int, min_spread: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    chat_hash = fernet.encrypt(str(chat_id).encode()).decode()
    cursor.execute("""
        UPDATE users SET min_spread = ? WHERE chat_hash = ?
    """, (min_spread, chat_hash))
    conn.commit()
    conn.close()

# --- API с ценами ---
API_URL = "http://5.129.209.25:8080/price/all"

async def fetch_spreads():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"Ошибка API: {resp.status}")
                    return None
    except Exception as e:
        print("Ошибка fetch_spreads:", e)
        return None

# --- Обработчики команд ---
async def cmd_start(message: types.Message):
    add_user(message.chat.id)
    await message.answer("✅ Ты подписан на уведомления об арбитраже!\n"
                         "Минимальный спред по умолчанию: 0.5%\n"
                         "Можно изменить: /setspread 1.2")

async def cmd_users(message: types.Message):
    users = get_all_users()
    txt = "👥 Пользователи:\n"
    for uid, spread in users:
        txt += f"- {uid}: {spread}%\n"
    await message.answer(txt)

async def cmd_setspread(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("❌ Используй формат: /setspread 1.0")
            return
        min_spread = float(parts[1])
        update_user_spread(message.chat.id, min_spread)
        await message.answer(f"✅ Минимальный спред установлен: {min_spread}%")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# --- Отправка уведомлений ---
async def notify_user(chat_id: int, text: str):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Ошибка отправки {chat_id}: {e}")

# --- Цикл уведомлений ---
async def notification_loop():
    while True:
        data = await fetch_spreads()
        if data:
            users = get_all_users()
            for token, t in data.items():
                if t.get("odos_price_usdt") and t.get("mexc_price_usdt"):
                    spread = ((t["mexc_price_usdt"] - t["odos_price_usdt"]) / t["odos_price_usdt"]) * 100
                    if spread > 0:
                        msg = (f"🪙 {token}\n"
                               f"DEX: {t['odos_price_usdt']:.6f} USDT\n"
                               f"CEX: {t['mexc_price_usdt']:.6f} USDT\n"
                               f"Spread: {spread:.2f}%")
                        for chat_id, min_spread in users:
                            if spread >= min_spread:
                                await notify_user(chat_id, msg)
        await asyncio.sleep(60)  # проверка раз в минуту

# --- Основной запуск ---
async def main():
    init_db()
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_users, Command(commands=["users"]))
    dp.message.register(cmd_setspread, Command(commands=["setspread"]))

    await asyncio.gather(
        dp.start_polling(bot),
        notification_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
