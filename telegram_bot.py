import os
import asyncio
import sqlite3
from cryptography.fernet import Fernet
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем .env_bot из текущей директории
load_dotenv(".env_bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FERNET_KEY = os.getenv("FERNET_KEY")

# Проверка, что переменные подгрузились
if not BOT_TOKEN or not FERNET_KEY:
    raise RuntimeError(".env_bot не загружен или переменные отсутствуют!")

# Fernet требует bytes
FERNET_KEY = FERNET_KEY.encode()
fernet = Fernet(FERNET_KEY)

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
            chat_hash TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def add_user(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    chat_hash = fernet.encrypt(str(chat_id).encode()).decode()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (chat_hash) VALUES (?)", (chat_hash,))
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_hash FROM users")
    rows = cursor.fetchall()
    conn.close()
    users = []
    for row in rows:
        try:
            users.append(fernet.decrypt(row[0].encode()).decode())
        except Exception:
            continue
    return users

# --- Обработчики команд ---
async def cmd_start(message: types.Message):
    add_user(message.chat.id)
    await message.answer(
        "Привет! Ты подписан на уведомления арбитража.\n"
        "Чтобы получать уведомления о новых спредах, бот должен быть активен."
    )

async def cmd_users(message: types.Message):
    users = get_all_users()
    await message.answer(f"Зарегистрированных пользователей: {len(users)}")

# --- Отправка уведомлений ---
async def notify_users(text: str):
    users = get_all_users()
    for chat_id in users:
        try:
            await bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Ошибка отправки уведомления {chat_id}: {e}")

# --- Тестовая функция для демонстрации ---
async def test_notification():
    while True:
        await asyncio.sleep(60)  # каждые 60 секунд
        await notify_users("Пример уведомления о спредах!")

# --- Основной запуск ---
async def main():
    init_db()
    
    # Регистрируем команды
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_users, Command(commands=["users"]))
    
    #
