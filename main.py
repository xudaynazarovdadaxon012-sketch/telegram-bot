import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router()

# 1. Rasmda ko'rsatilgan Inline Menyu (Tugmalar)
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url="https://sizning-miniapp-url.com"))],
            [
                InlineKeyboardButton(text="🤖 Sun'iy Intellekt (AI)", callback_data="ai_chat"),
                InlineKeyboardButton(text="🎨 AI Rasm Yaratish", callback_data="ai_image")
            ],
            [
                InlineKeyboardButton(text="📥 Video Yuklagich", callback_data="video_downloader"),
                InlineKeyboardButton(text="📈 Kripto & Oltin", callback_data="crypto_gold")
            ],
            [
                InlineKeyboardButton(text="🔗 Link Qisqartirish", callback_data="link_shortener"),
                InlineKeyboardButton(text="🔤 Matn Tarjimon", callback_data="translator")
            ],
            [
                InlineKeyboardButton(text="📲 QR-Kod Yaratish", callback_data="qr_code"),
                InlineKeyboardButton(text="🧮 Aqlli Kalkulyator", callback_data="calculator")
            ],
            [
                InlineKeyboardButton(text="🌤 Aniq Ob-havo", callback_data="weather"),
                InlineKeyboardButton(text="💎 Valyuta kurslari", callback_data="currency")
            ],
            [InlineKeyboardButton(text="📝 Shaxsiy Eslatmalar", callback_data="notes")],
            [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")]
        ]
    )
    return keyboard

# Start buyrug'i kelganda menyuni chiqarish
@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_keyboard())

# Har bir tugma uchun Callback Handler'lar
@router.callback_query(F.data == "ai_chat")
async def ai_chat_handler(call: types.CallbackQuery):
    await call.message.answer("Sun'iy Intellekt bo'limi tanlandi.")
    await call.answer()

# (Boshqa barcha tugmalaringiz uchun handler'lar shu tarzda davom etadi...)


# 2. Render uyquga ketmasligi uchun Health-Check web-server
async def handle_ping(request):
    return web.Response(text="Bot is running active!")

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    # aiohttp serverini ishga tushirish
    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
