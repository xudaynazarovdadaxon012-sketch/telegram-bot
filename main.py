import os
import sqlite3
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import aiohttp

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAHCVZH2bz5XIaVszG6OwJo2V2-tnuzPWWA")
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- SQLITE DATABASE ---
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    created_at TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    note_text TEXT,
    created_at TEXT
)
""")
conn.commit()

class NoteState(StatesGroup):
    waiting_for_note = State()

def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/miniapp.html"))],
            [types.KeyboardButton(text="🧮 Aqlli Kalkulyator"), types.KeyboardButton(text="🌤 Aniq Ob-havo")],
            [types.KeyboardButton(text="💎 Valyuta kurslari"), types.KeyboardButton(text="📝 Shaxsiy Eslatmalar")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Foydalanuvchi"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)", 
                   (user_id, username, now))
    conn.commit()

    await message.answer(
        f"✨ **Xush kelibsiz, {message.from_user.first_name}!**\n\n"
        f"⚡ **Telegram Ultra-Premium Bot** xizmatidan foydalanishingiz mumkin.\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# --- INTERAKTIV DINAMIK KALKULYATOR ---
user_calc = {}

def get_calc_keyboard(expr="0"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📊 Disp: {expr}", callback_data="calc_noop")],
        [InlineKeyboardButton(text="🧹 C", callback_data="calc_clear"), InlineKeyboardButton(text="(", callback_data="calc_("), InlineKeyboardButton(text=")", callback_data="calc_)"), InlineKeyboardButton(text="÷", callback_data="calc_/")],
        [InlineKeyboardButton(text="7", callback_data="calc_7"), InlineKeyboardButton(text="8", callback_data="calc_8"), InlineKeyboardButton(text="9", callback_data="calc_9"), InlineKeyboardButton(text="×", callback_data="calc_*")],
        [InlineKeyboardButton(text="4", callback_data="calc_4"), InlineKeyboardButton(text="5", callback_data="calc_5"), InlineKeyboardButton(text="6", callback_data="calc_6"), InlineKeyboardButton(text="-", callback_data="calc_-")],
        [InlineKeyboardButton(text="1", callback_data="calc_1"), InlineKeyboardButton(text="2", callback_data="calc_2"), InlineKeyboardButton(text="3", callback_data="calc_3"), InlineKeyboardButton(text="+", callback_data="calc_+")],
        [InlineKeyboardButton(text="0", callback_data="calc_0"), InlineKeyboardButton(text=".", callback_data="calc_."), InlineKeyboardButton(text="🧮 =", callback_data="calc_eval")]
    ])

@dp.message(F.text == "🧮 Aqlli Kalkulyator")
async def show_calculator(message: types.Message):
    user_calc[message.from_user.id] = ""
    await message.answer("🧮 **Aqlli Kalkulyator:**", reply_markup=get_calc_keyboard("0"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("calc_"))
async def calc_callback(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.replace("calc_", "")
    current = user_calc.get(user_id, "")

    if action == "noop":
        await call.answer()
        return
    elif action == "clear":
        current = ""
    elif action == "eval":
        try:
            safe_expr = current.replace("×", "*").replace("÷", "/")
            current = str(eval(safe_expr))
        except Exception:
            current = "Xatolik"
    else:
        if action in ["*", "/"]:
            char = "×" if action == "*" else "÷"
        else:
            char = action
        current += char

    user_calc[user_id] = current
    disp = current if current != "" else "0"
    try:
        await call.message.edit_reply_markup(reply_markup=get_calc_keyboard(disp))
    except Exception:
        pass
    await call.answer()

# --- ANIQ OB-HAVO (Open-Meteo API) ---
CITIES = {
    "toshkent": ("Toshkent", 41.2995, 69.2401),
    "andijon": ("Andijon", 40.7821, 72.3442),
    "fargona": ("Farg'ona", 40.3842, 71.7843),
    "namangan": ("Namangan", 41.0011, 71.6683),
    "samarqand": ("Samarqand", 39.6542, 66.9597),
    "buxoro": ("Buxoro", 39.7747, 64.4286),
    "xorazm": ("Urganch", 41.5500, 60.6333),
    "navoiy": ("Navoiy", 40.0844, 65.3792),
    "qashqadaryo": ("Qarshi", 38.8605, 65.7899),
    "surxondaryo": ("Termiz", 37.2242, 67.2783),
    "jizzax": ("Jizzax", 40.1158, 67.8422),
    "sirdaryo": ("Guliston", 40.4897, 68.7842),
    "nukus": ("Nukus", 42.4603, 59.6166)
}

@dp.message(F.text == "🌤 Aniq Ob-havo")
async def show_weather_cities(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Toshkent", callback_data="w_toshkent"), InlineKeyboardButton(text="📍 Andijon", callback_data="w_andijon")],
        [InlineKeyboardButton(text="📍 Farg'ona", callback_data="w_fargona"), InlineKeyboardButton(text="📍 Namangan", callback_data="w_namangan")],
        [InlineKeyboardButton(text="📍 Samarqand", callback_data="w_samarqand"), InlineKeyboardButton(text="📍 Buxoro", callback_data="w_buxoro")],
        [InlineKeyboardButton(text="📍 Xorazm", callback_data="w_xorazm"), InlineKeyboardButton(text="📍 Navoiy", callback_data="w_navoiy")],
        [InlineKeyboardButton(text="📍 Qashqadaryo", callback_data="w_qashqadaryo"), InlineKeyboardButton(text="📍 Surxondaryo", callback_data="w_surxondaryo")],
        [InlineKeyboardButton(text="📍 Jizzax", callback_data="w_jizzax"), InlineKeyboardButton(text="📍 Sirdaryo", callback_data="w_sirdaryo")],
        [InlineKeyboardButton(text="📍 Qoraqalpog'iston", callback_data="w_nukus")]
    ])
    await message.answer("🌤 **Kerakli hududni tanlang:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("w_"))
async def get_real_weather(call: CallbackQuery):
    city_key = call.data.replace("w_", "")
    if city_key in CITIES:
        name, lat, lon = CITIES[city_key]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    curr = data.get("current_weather", {})
                    temp = curr.get("temperature", "N/A")
                    wind = curr.get("windspeed", "N/A")
                    
                    text = (
                        f"🌤 **{name} bo'yicha Ob-havo:**\n\n"
                        f"🌡 Harorat: **{temp}°C**\n"
                        f"💨 Shamol: **{wind} km/h**\n"
                        f"⚡ *Ma'lumotlar real vaqt rejimida yangilandi.*"
                    )
                    await call.message.answer(text, parse_mode="Markdown")
        except Exception:
            await call.message.answer("Ob-havoni yuklashda xatolik yuz berdi.")
    await call.answer()

# --- VALYUTA KURSLARI ---
@dp.message(F.text == "💎 Valyuta kurslari")
async def get_currency(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/") as resp:
                data = await resp.json()
                usd = next((i for i in data if i["Ccy"] == "USD"), None)
                eur = next((i for i in data if i["Ccy"] == "EUR"), None)
                rub = next((i for i in data if i["Ccy"] == "RUB"), None)

                text = "📊 **Markaziy Bank rasmiy kurslari:**\n\n"
                if usd: text += f"🇺🇸 1 USD = **{usd['Rate']}** so'm\n"
                if eur: text += f"🇪🇺 1 EUR = **{eur['Rate']}** so'm\n"
                if rub: text += f"🇷🇺 1 RUB = **{rub['Rate']}** so'm\n"
                await message.answer(text, parse_mode="Markdown")
    except Exception:
        await message.answer("Valyutani olishda xatolik bo'ldi.")

# --- SHAXSIY ESLATMALAR ---
@dp.message(F.text == "📝 Shaxsiy Eslatmalar")
async def show_notes(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute("SELECT id, note_text, created_at FROM notes WHERE user_id = ?", (user_id,))
    notes = cursor.fetchall()
    
    if notes:
        res = "📝 **Sizning eslatmalaringiz:**\n\n"
        for n in notes:
            res += f"📌 **{n[0]}**. {n[1]} _({n[2]})_\n"
        res += "\nYangi eslatma matnini yuboring:"
    else:
        res = "Sizda hali eslatma yo'q.\nYangi eslatma yozib yuboring:"

    await state.set_state(NoteState.waiting_for_note)
    await message.answer(res, parse_mode="Markdown")

@dp.message(NoteState.waiting_for_note)
async def save_note(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO notes (user_id, note_text, created_at) VALUES (?, ?, ?)", (user_id, message.text, now))
    conn.commit()
    
    await message.answer("✅ Eslatma muvaffaqiyatli saqlandi!", reply_markup=main_keyboard())
    await state.clear()

# --- AIOHTTP WEB SERVER & STATIC FILE SERVE ---
async def init_app():
    app = web.Application()
    app.router.add_get('/health', lambda r: web.Response(text="Server Online"))
    current_dir = os.path.dirname(os.path.realpath(__file__))
    app.router.add_static('/', path=current_dir, name='static', show_index=True)
    return app

async def main():
    port = int(os.environ.get("PORT", 10000))
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    logging.info(f"Port {port} ishlamoqda.")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
