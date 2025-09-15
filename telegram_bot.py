import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from cryptography.fernet import Fernet

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Токен бота
FERNET_KEY = os.getenv("FERNET_KEY").encode()  # Ключ для шифрования (генерируешь один раз)
DB_FILE = "subscribers.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY)

# --- Работа с БД ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id_enc TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_subscriber(chat_id: int):
    enc = fernet.encrypt(str(chat_id).encode()).decode()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO subscribers (chat_id_enc) VALUES (?)", (enc,))
    conn.commit()
    conn.close()

def remove_subscriber(chat_id: int):
    enc = fernet.encrypt(str(chat_id).encode()).decode()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscribers WHERE chat_id_enc=?", (enc,))
    conn.commit()
    conn.close()

def get_subscribers():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT chat_id_enc FROM subscribers")
    rows = cur.fetchall()
    conn.close()
    return [int(fernet.decrypt(row[0].encode()).decode()) for row in rows]

# --- Telegram команды ---
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    add_subscriber(message.chat.id)
    await message.answer("✅ Вы подписаны на уведомления об арбитраже")

@dp.message(commands=["stop"])
async def cmd_stop(message: types.Message):
    remove_subscriber(message.chat.id)
    await message.answer("❌ Вы отписались от уведомлений")

# --- Отправка уведомлений ---
async def send_alert(text: str):
    for chat_id in get_subscribers():
        try:
            await bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Ошибка при отправке {chat_id}: {e}")

# --- Запуск ---
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
