import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAFJ3U60hJC3XzpQb2IJYTCy23qmtuiv79M")
# Render domeningiz
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- START BUYRUG'I ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎮 Mini App (O'yinlar)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/miniapp.html"))],
            [types.KeyboardButton(text="🧮 Kalkulyator")]
        ],
        resize_keyboard=True
    )
    await message.answer("Xush kelibsiz! O'yinlarni o'ynash uchun tugmani bosing:", reply_markup=kb)

# --- KALKULYATOR TUGMALARI (4x5 tartibida) ---
@dp.message(lambda msg: msg.text == "🧮 Kalkulyator")
async def show_calculator(message: types.Message):
    calc_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="C", callback_data="calc_clear"), InlineKeyboardButton(text="(", callback_data="calc_("), InlineKeyboardButton(text=")", callback_data="calc_)"), InlineKeyboardButton(text="÷", callback_data="calc_/")],
        [InlineKeyboardButton(text="7", callback_data="calc_7"), InlineKeyboardButton(text="8", callback_data="calc_8"), InlineKeyboardButton(text="9", callback_data="calc_9"), InlineKeyboardButton(text="×", callback_data="calc_*")],
        [InlineKeyboardButton(text="4", callback_data="calc_4"), InlineKeyboardButton(text="5", callback_data="calc_5"), InlineKeyboardButton(text="6", callback_data="calc_6"), InlineKeyboardButton(text="-", callback_data="calc_-")],
        [InlineKeyboardButton(text="1", callback_data="calc_1"), InlineKeyboardButton(text="2", callback_data="calc_2"), InlineKeyboardButton(text="3", callback_data="calc_3"), InlineKeyboardButton(text="+", callback_data="calc_+")],
        [InlineKeyboardButton(text="0", callback_data="calc_0"), InlineKeyboardButton(text=".", callback_data="calc_."), InlineKeyboardButton(text="=", callback_data="calc_eval")]
    ])
    await message.answer("Kalkulyator:", reply_markup=calc_kb)

# --- AIOHTTP WEB SERVER ---
async def init_app():
    app = web.Application()
    
    # Ping loglari uchun
    async def health(request):
        return web.Response(text="Bot Status: OK")
    
    app.router.add_get('/health', health)
    
    # Barcha HTML/JS/CSS fayllarni static sifat tarqatish
    current_dir = os.path.dirname(os.path.realpath(__file__))
    app.router.add_static('/', path=current_dir, name='static', show_index=True)
    
    return app

async def main():
    port = int(os.environ.get("PORT", 10000))
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server port {port} da ishga tushdi.")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
