import os
import asyncio
import sqlite3
from cryptography.fernet import Fernet
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# ---- Настройки ----
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FERNET_KEY = os.getenv("FERNET_KEY").encode()  # Должен быть 32 байта в base64
fernet = Fernet(FERNET_KEY)

DB_PATH = "telegram_users.db"

# ---- Бот и диспетчер ----
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---- SQLite ----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_hash TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def add_user(chat_id: int):
    """Хешируем chat_id и сохраняем в базе, если его там нет."""
    chat_hash = fernet.encrypt(str(chat_id).encode()).decode()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_hash) VALUES (?)", (chat_hash,))
    conn.commit()
    conn.close()

def get_all_users():
    """Возвращает список всех chat_id для рассылки (расшифрованные)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_hash FROM users")
    rows = c.fetchall()
    conn.close()
    return [int(fernet.decrypt(row[0].encode()).decode()) for row in rows]

# ---- Команды бота ----
@dp.message(Command("start"))
async def cmd_start(message: Message):
    add_user(message.chat.id)
    await message.answer("Привет! Ты подписался на уведомления о арбитраже.")

# ---- Уведомления ----
async def send_alert(token_name: str, spread: float):
    """Пример функции рассылки уведомлений всем пользователям."""
    users = get_all_users()
    for chat_id in users:
        try:
            await bot.send_message(
                chat_id,
                f"Арбитраж: {token_name}\nСпред: {spread:.2f}%"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение {chat_id}: {e}")

# ---- Основной запуск ----
async def main():
    init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
# ---- V2 ----
