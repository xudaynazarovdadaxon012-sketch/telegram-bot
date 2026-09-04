import os
import sqlite3
import logging
import asyncio
from aiohttp import web
from cryptography.fernet import Fernet

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# Environmental Configurations
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8898979946))  # O'zingizning ID raqamingiz

# AES-256 Shifrlash uchun kalit yaratish yoki yuklash
KEY_FILE = "secret.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        FERNET_KEY = f.read()
else:
    FERNET_KEY = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(FERNET_KEY)

cipher_suite = Fernet(FERNET_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ==================== DATABASE ARCHITECTURE ====================
def init_db():
    conn = sqlite3.connect("platform_database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0,
            coins INTEGER DEFAULT 0,
            is_vip INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ulangan external accounts (OAuth Tokenlar) jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_name TEXT,
            encrypted_token BLOB,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

def register_user(user_id: int, full_name: str, username: str):
    conn = sqlite3.connect("platform_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, full_name, username) VALUES (?, ?, ?)", 
                       (user_id, full_name, username))
    else:
        cursor.execute("UPDATE users SET full_name = ?, username = ? WHERE user_id = ?", 
                       (full_name, username, user_id))
    conn.commit()
    conn.close()

def encrypt_data(data: str) -> bytes:
    return cipher_suite.encrypt(data.encode('utf-8'))

def decrypt_data(encrypted_data: bytes) -> str:
    return cipher_suite.decrypt(encrypted_data).decode('utf-8')

# ==================== BOT HANDLERS ====================
@router.message(CommandStart())
async def cmd_start(message: Message):
    register_user(message.from_user.id, message.from_user.full_name, message.from_user.username or "")
    await message.answer(
        "✨ **Prime Mini App Platformasiga Xush Kelibsiz!**\n\n"
        "Quyidagi havola orqali markazlashtirilgan boshqaruv panelini oching."
    )

# ==================== API & SERVER ====================
async def handle_miniapp(request):
    try:
        with open("miniapp.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception as e:
        return web.Response(text=f"App Load Error: {e}", status=500)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_miniapp)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ==================== ENGINE ENTRYPOINT ====================
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    asyncio.create_task(start_web_server())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
