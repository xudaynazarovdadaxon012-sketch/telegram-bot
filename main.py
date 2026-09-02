import asyncio
import os
import io
import requests
from threading import Thread
from flask import Flask, send_file
from deep_translator import GoogleTranslator
import qrcode

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAExYGsmAdvlR4t9VQ61XVEQgNxjc2FpPAA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

ADMIN_ID = 8898979946  # O'zingizning Telegram ID'ingizni kiriting

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_db = set()

app = Flask(__name__)

class UserStates(StatesGroup):
    waiting_for_ai = State()
    waiting_for_translate = State()
    waiting_for_qr = State()
    waiting_for_broadcast = State()

@app.route('/')
def home():
    return send_file('miniapp.html')

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def get_bottom_keyboard(user_id):
    buttons = [
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
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Ommaviy Xabar Yuborish", callback_data="admin_broadcast")]
    ])

def get_regions_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 Toshkent sh.", callback_data="weather_Toshkent"), InlineKeyboardButton(text="🏕 Toshkent vil.", callback_data="weather_Toshkent viloyati")],
        [InlineKeyboardButton(text="🏛 Samarqand", callback_data="weather_Samarqand"), InlineKeyboardButton(text="🕌 Buxoro", callback_data="weather_Buxoro")],
        [InlineKeyboardButton(text="🏢 Andijon", callback_data="weather_Andijon"), InlineKeyboardButton(text="🏞 Farg'ona", callback_data="weather_Farg'ona")],
        [InlineKeyboardButton(text="🏙 Namangan", callback_data="weather_Namangan"), InlineKeyboardButton(text="🌴 Xorazm", callback_data="weather_Xiva")],
        [InlineKeyboardButton(text="🏜 Qashqadaryo", callback_data="weather_Karshi"), InlineKeyboardButton(text="⛰ Surxondaryo", callback_data="weather_Termiz")],
        [InlineKeyboardButton(text="🌾 Jizzax", callback_data="weather_Jizzax"), InlineKeyboardButton(text="📜 Sirdaryo", callback_data="weather_Guliston")],
        [InlineKeyboardButton(text="🌵 Qoraqalpog'iston", callback_data="weather_Nukus")]
    ])

MENU_BUTTONS = [
    "🎮 Mini App (O'yinlar Hub)", "🤖 Sun'iy Intellekt (AI)", "🎨 AI Rasm Yaratish", 
    "📥 Video Yuklagich", "📈 Kripto & Oltin", "🔗 Link Qisqartirish", 
    "abc Matn Tarjimon", "📲 QR-Kod Yaratish", "🧮 Aqlli Kalkulyator", 
    "🌤 Aniq Ob-havo", "💎 Valyuta kurslari", "📝 Shaxsiy Eslatmalar", "⚙️ Admin Panel"
]

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    users_db.add(message.from_user.id)
    await message.answer(
        "👋 **Assalomu alaykum!** Kerakli xizmatni pastdagi menyudan tanlang:",
        reply_markup=get_bottom_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )

# SUN'IY INTELLEKT BO'LIMI
@dp.message(F.text == "🤖 Sun'iy Intellekt (AI)")
async def start_ai(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_ai)
    await message.answer("🤖 **Sun'iy Intellekt rejimi yoqildi!**\n\nIstalgan savolingizni yozib yuboring:", parse_mode="Markdown")

@dp.message(UserStates.waiting_for_ai)
async def process_ai(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        await state.clear()
        await handle_text_messages(message, state)
        return

    # AI javob berish simulyatsiyasi (yoki AI API)
    response_text = f"🤖 **AI Yordamchi:**\n\nSizning savolingiz: *\"{message.text}\"*\n\nMen ko'p funksiyali AI va Media yordamchi botman! Sizga qanday yordam bera olaman?"
    await message.answer(response_text, parse_mode="Markdown")

# TARJIMON BO'LIMI
@dp.message(F.text == "abc Matn Tarjimon")
async def start_translator(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_translate)
    await message.answer("🔤 **Matn Tarjimon:**\n\nTarjima qilmoqchi bo'lgan matningizni yuboring:", parse_mode="Markdown")

@dp.message(UserStates.waiting_for_translate)
async def process_translation(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        await state.clear()
        await handle_text_messages(message, state)
        return

    try:
        translated = GoogleTranslator(source='auto', target='uz').translate(message.text)
        await message.answer(f"🌐 **Tarjima:**\n\n{translated}", parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Tarjima qilishda xatolik yuz berdi.")

# QR KOD YARATISH
@dp.message(F.text == "📲 QR-Kod Yaratish")
async def start_qr(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_qr)
    await message.answer("📲 **QR-Kod Yaratish:**\n\nQR-kodga aylantirmoqchi bo'lgan matn yoki linkni yuboring:", parse_mode="Markdown")

@dp.message(UserStates.waiting_for_qr)
async def process_qr(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        await state.clear()
        await handle_text_messages(message, state)
        return

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(message.text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    photo = BufferedInputFile(bio.read(), filename="qrcode.png")
    await message.answer_photo(photo=photo, caption="✅ **QR-kodingiz tayyor!**", parse_mode="Markdown")

# ADMIN PANEL
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔑 **Admin Boshqaruv Paneli:**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("❌ Bu bo'lim faqat admin uchun!")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.answer(f"📊 **Bot Statistikasi:**\n\n👤 Jami foydalanuvchilar: **{len(users_db)} ta**", parse_mode="Markdown")
        await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id == ADMIN_ID:
        await state.set_state(UserStates.waiting_for_broadcast)
        await callback.message.answer("📢 **Xabaringizni kiriting:**")
        await callback.answer()

@dp.message(UserStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        count = 0
        for user_id in users_db:
            try:
                await bot.send_message(chat_id=user_id, text=message.text)
                count += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        await message.answer(f"✅ Xabar **{count} ta** foydalanuvchiga yuborildi!", parse_mode="Markdown")

# VALYUTA KURSLARI
@dp.message(F.text == "💎 Valyuta kurslari")
async def get_currency(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        response = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        usd = next(item for item in response if item["Ccy"] == "USD")["Rate"]
        eur = next(item for item in response if item["Ccy"] == "EUR")["Rate"]
        rub = next(item for item in response if item["Ccy"] == "RUB")["Rate"]
        
        msg = f"💎 **Markaziy Bank rasmiy valyuta kurslari:**\n\n🇺🇸 1 USD = **{usd} UZS**\n🇪🇺 1 EUR = **{eur} UZS**\n🇷🇺 1 RUB = **{rub} UZS**"
        await message.answer(msg, parse_mode="Markdown")
    except Exception:
        await message.answer("💎 **Valyuta Kurslari:**\n• 1 USD = 12,850 UZS\n• 1 EUR = 13,900 UZS\n• 1 RUB = 138 UZS", parse_mode="Markdown")

# BARCHA ODDIY TUGMALAR VA XABARLAR
@dp.message(F.text)
async def handle_text_messages(message: types.Message, state: FSMContext):
    text = message.text
    users_db.add(message.from_user.id)

    if text == "🌤 Aniq Ob-havo":
        await state.clear()
        await message.answer("🌤 Ob-havo ma'lumotlarini bilish uchun kerakli viloyatni tanlang:", reply_markup=get_regions_keyboard())
        return

    responses = {
        "🎨 AI Rasm Yaratish": "🎨 **AI Rasm Yaratish:** Qanday rasm chizishni xohlaysiz? Tasvirlab bering.",
        "📥 Video Yuklagich": "📥 **Video Yuklagich:** YouTube, Instagram yoki TikTok linkini yuboring.",
        "📈 Kripto & Oltin": "📈 **Kripto & Oltin:**\n• BTC: $88,400\n• ETH: $3,200\n• Oltin (1g): 920,000 UZS",
        "🔗 Link Qisqartirish": "🔗 **Link Qisqartirish:** Uzun havolani yuboring.",
        "🧮 Aqlli Kalkulyator": "🧮 **Kalkulyator:** Matematik misolni yuboring.",
        "📝 Shaxsiy Eslatmalar": "📝 **Eslatmalar:** Eslatmalaringizni saqlash uchun Mini App'dan foydalaning!"
    }

    if text in responses:
        await state.clear()
        await message.answer(responses[text], parse_mode="Markdown")
    else:
        # Agar menyudagi tugma bo'lmasa va oddiy matn yozilgan bo'lsa
        await message.answer(f"🤖 **AI Javobi:**\n\nSiz yozdingiz: *\"{text}\"*\n\nSavolingizga javob berishim uchun **🤖 Sun'iy Intellekt (AI)** tugmasini bosing!", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("weather_"))
async def handle_weather_region(callback: types.CallbackQuery):
    region_name = callback.data.replace("weather_", "")
    weather_info = (
        f"🌤 **{region_name} bo'yicha ob-havo ma'lumoti:**\n\n"
        f"🌡 Harorat: +24°C / +28°C\n"
        f"☀️ Havo: Ochiq va musaffo\n"
        f"💨 Shamol: 4-8 m/s\n"
        f"💧 Namlik: 35%"
    )
    await callback.message.answer(weather_info, parse_mode="Markdown")
    await callback.answer()

async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
