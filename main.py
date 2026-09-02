import asyncio
import os
from threading import Thread
from flask import Flask, send_file

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAExYGsmAdvlR4t9VQ61XVEQgNxjc2FpPAA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return send_file('miniapp.html')

def run_flask():
    # Render avto-belgilaydigan PORT'ni olish va ishga tushirish
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ASOSIY KLAVIATURA
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton(text="🤖 Sun'iy Intellekt (AI)", callback_data="btn_ai"),
            InlineKeyboardButton(text="🎨 AI Rasm Yaratish", callback_data="btn_draw")
        ],
        [
            InlineKeyboardButton(text="📥 Video Yuklagich", callback_data="btn_video"),
        ],
        [
            InlineKeyboardButton(text="📈 Kripto & Oltin", callback_data="btn_crypto"),
            InlineKeyboardButton(text="🔗 Link Qisqartirish", callback_data="btn_shorten")
        ],
        [
            InlineKeyboardButton(text="abc Matn Tarjimon", callback_data="btn_translate"),
            InlineKeyboardButton(text="📲 QR-Kod Yaratish", callback_data="btn_qr")
        ],
        [
            InlineKeyboardButton(text="🧮 Aqlli Kalkulyator", callback_data="btn_calc"),
            InlineKeyboardButton(text="🌤 Aniq Ob-havo", callback_data="btn_weather")
        ],
        [
            InlineKeyboardButton(text="💎 Valyuta kurslari", callback_data="btn_currency"),
            InlineKeyboardButton(text="📝 Shaxsiy Eslatmalar", callback_data="btn_notes")
        ]
    ])
    return keyboard

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Kerakli xizmatni tanlang:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data.startswith("btn_"))
async def handle_buttons(callback: types.CallbackQuery):
    action = callback.data.replace("btn_", "")
    
    responses = {
        "ai": "🤖 **Sun'iy Intellekt:** Savolingizni matn ko'rinishida yuboring!",
        "draw": "🎨 **AI Rasm Yaratish:** Qanday rasm chizishni xohlaysiz? Tasvirlab bering.",
        "video": "📥 **Video Yuklagich:** YouTube, Instagram yoki TikTok linkini yuboring.",
        "ocr": "📄 **Rasmdan Matn O'qish:** Ichida yozuvi bor rasmni yuboring.",
        "crypto": "📈 **Kripto & Oltin:**\n• BTC: $88,400\n• ETH: $3,200\n• Oltin (1g): 920,000 UZS",
        "shorten": "🔗 **Link Qisqartirish:** Uzun havolani yuboring.",
        "translate": "abc **Matn Tarjimon:** Tarjima qilish uchun matn yuboring.",
        "qr": "📲 **QR-Kod Yaratish:** QR-kodga aylantirmoqchi bo'lgan matn yoki linkni kiriting.",
        "calc": "🧮 **Kalkulyator:** Matematik misolni yuboring (Masalan: `45 * 12 + 100`).",
        "weather": "🌤 **Aniq Ob-havo:** Shahringiz nomini yuboring (Masalan: *Toshkent*).",
        "currency": "💎 **Valyuta Kurslari:**\n• 1 USD = 12,850 UZS\n• 1 EUR = 13,900 UZS\n• 1 RUB = 138 UZS",
        "notes": "📝 **Eslatmalar:** Eslatmalaringizni saqlash uchun Mini App'dan foydalaning!"
    }
    
    msg = responses.get(action, "Xizmat tanlandi.")
    await callback.message.answer(msg, parse_mode="Markdown")
    await callback.answer()

async def main():
    # Web serverni fonda alohida oqimda yurgizamiz
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Botingizni ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
