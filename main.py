import asyncio
import os
from threading import Thread
from flask import Flask, send_file

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    WebAppInfo
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAExYGsmAdvlR4t9VQ61XVEQgNxjc2FpPAA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)

@app.route('/')
def home():
    return send_file('miniapp.html')

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# PASTDAGI MENYU ("Rasmdan Matn O'qish" olib tashlangan va tekislangan)
def get_bottom_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=WEBAPP_URL))],
            [
                KeyboardButton(text="🤖 Sun'iy Intellekt (AI)"),
                KeyboardButton(text="🎨 AI Rasm Yaratish")
            ],
            [
                KeyboardButton(text="📥 Video Yuklagich"),
                KeyboardButton(text="📈 Kripto & Oltin")
            ],
            [
                KeyboardButton(text="🔗 Link Qisqartirish"),
                KeyboardButton(text="abc Matn Tarjimon")
            ],
            [
                KeyboardButton(text="📲 QR-Kod Yaratish"),
                KeyboardButton(text="🧮 Aqlli Kalkulyator")
            ],
            [
                KeyboardButton(text="🌤 Aniq Ob-havo"),
                KeyboardButton(text="💎 Valyuta kurslari")
            ],
            [
                KeyboardButton(text="📝 Shaxsiy Eslatmalar")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Kerakli xizmatni tanlang:",
        reply_markup=get_bottom_keyboard()
    )

@dp.message(F.text)
async def handle_text_messages(message: types.Message):
    text = message.text

    responses = {
        "🤖 Sun'iy Intellekt (AI)": "🤖 **Sun'iy Intellekt:** Savolingizni matn ko'rinishida yuboring!",
        "🎨 AI Rasm Yaratish": "🎨 **AI Rasm Yaratish:** Qanday rasm chizishni xohlaysiz? Tasvirlab bering.",
        "📥 Video Yuklagich": "📥 **Video Yuklagich:** YouTube, Instagram yoki TikTok linkini yuboring.",
        "📈 Kripto & Oltin": "📈 **Kripto & Oltin:**\n• BTC: $88,400\n• ETH: $3,200\n• Oltin (1g): 920,000 UZS",
        "🔗 Link Qisqartirish": "🔗 **Link Qisqartirish:** Uzun havolani yuboring.",
        "abc Matn Tarjimon": "abc **Matn Tarjimon:** Tarjima qilish uchun matn yuboring.",
        "📲 QR-Kod Yaratish": "📲 **QR-Kod Yaratish:** QR-kodga aylantirmoqchi bo'lgan matn yoki linkni kiriting.",
        "🧮 Aqlli Kalkulyator": "🧮 **Kalkulyator:** Matematik misolni yuboring.",
        "🌤 Aniq Ob-havo": "🌤 **Aniq Ob-havo:** Shahringiz nomini yuboring.",
        "💎 Valyuta kurslari": "💎 **Valyuta Kurslari:**\n• 1 USD = 12,850 UZS\n• 1 EUR = 13,900 UZS\n• 1 RUB = 138 UZS",
        "📝 Shaxsiy Eslatmalar": "📝 **Eslatmalar:** Eslatmalaringizni saqlash uchun Mini App'dan foydalaning!"
    }

    if text in responses:
        await message.answer(responses[text], parse_mode="Markdown")

async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
