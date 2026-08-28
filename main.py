import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web

BOT_TOKEN = "8760162640:AAFJ3U60hJC3XzpQb2IJYTCy23qmtuiv79M"  # Bu yerga BotFather'dan olingan tokeningizni yozing
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- RENDER UCHUN DUMMY WEB SERVER (Port scan xatosini yo'qotadi) ---
async def handle(request):
    return web.Response(text="Bot va Mini App faol ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server port {port} da ishga tushdi.")

# --- DATABASE SOZLAMALARI ---
def init_db():
    conn = sqlite3.connect("game_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance INTEGER DEFAULT 0,
            referrer_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- BOT BUYRUQLARI ---
@dp.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Mini App'ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(f"Xush kelibsiz, {full_name}!\nMini App'ni pastdagi tugma orqali oching:", reply_markup=keyboard)

async def main():
    # Render port xatosi bermasligi uchun web serverni parallel ishga tushiramiz
    await start_web_server()
    print("Bot polling rejimida ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
