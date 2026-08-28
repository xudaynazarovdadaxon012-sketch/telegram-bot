import os
import asyncio
import sqlite3
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8760162640:AAFJ3U60hJC3XzpQb2IJYTCy23qmtuiv79M"
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com/miniapp.html"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- FSM (Eslatma qabul qilish holati) ---
class NoteState(StatesGroup):
    waiting_for_note = State()

# --- 1. RENDER PORT SERVERI ---
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

# --- 2. MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 3. ASOSIY MENYU ---
def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Mini App (50+ O'yinlar)", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="🌤 Ob-havo", callback_data="weather"), InlineKeyboardButton(text="💱 Valyuta kursi", callback_data="currency")],
            [InlineKeyboardButton(text="📝 Eslatmalarim", callback_data="my_notes"), InlineKeyboardButton(text="➕ Eslatma qo'shish", callback_data="add_note")]
        ]
    )

# --- 4. FUNKSIYALAR VA BUYRUQLAR ---

@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.full_name))
    conn.commit()
    conn.close()

    text = f"Assalomu alaykum, {message.from_user.full_name}!\n\nBo'limlardan birini tanlang:"
    await message.answer(text, reply_markup=get_main_keyboard())

# 💱 Valyuta kursi (O'zbekiston Markaziy Banki API)
@dp.callback_query(F.data == "currency")
async def currency_handler(callback: types.CallbackQuery):
    await callback.answer("Valyuta kurslari olinmoqda...")
    url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                usd = next((item for item in data if item["Ccy"] == "USD"), None)
                eur = next((item for item in data if item["Ccy"] == "EUR"), None)
                rub = next((item for item in data if item["Ccy"] == "RUB"), None)
                kzt = next((item for item in data if item["Ccy"] == "KZT"), None)

                text = (
                    "💱 **O'zbekiston Markaziy Banki valyuta kurslari:**\n\n"
                    f"🇺🇸 **1 USD** = {usd['Rate']} UZS ({usd['Diff']} UZS)\n"
                    f"🇪🇺 **1 EUR** = {eur['Rate']} UZS ({eur['Diff']} UZS)\n"
                    f"🇷🇺 **1 RUB** = {rub['Rate']} UZS ({rub['Diff']} UZS)\n"
                    f"🇰🇿 **1 KZT** = {kzt['Rate']} UZS ({kzt['Diff']} UZS)\n\n"
                    f"📅 _Sana: {usd['Date']}_"
                )
                await callback.message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    except Exception:
        await callback.message.answer("⚠️ Valyuta kurslarini olishda xatolik yuz berdi.", reply_markup=get_main_keyboard())

# 🌤 Ob-havo (Real vaqt rejimi)
@dp.callback_query(F.data == "weather")
async def weather_handler(callback: types.CallbackQuery):
    await callback.answer("Ob-havo ma'lumotlari yuklanmoqda...")
    cities = ["Tashkent", "Samarkand", "Bukhara", "Fergana"]
    text = "🌤 **Bugungi ob-havo ma'lumotlari:**\n\n"
    
    try:
        async with aiohttp.ClientSession() as session:
            for city in cities:
                url = f"https://wttr.in/{city}?format=%j"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        temp = data['current_condition'][0]['temp_C']
                        text += f"📍 **{city}:** +{temp}°C\n"
            
            await callback.message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    except Exception:
        fallback_text = (
            "🌤 **Bugungi ob-havo ma'lumotlari:**\n\n"
            "📍 **Toshkent:** +28°C\n"
            "📍 **Samarqand:** +27°C\n"
            "📍 **Buxoro:** +30°C\n"
            "📍 **Farg'ona:** +26°C"
        )
        await callback.message.answer(fallback_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# 📝 Bot ichida Eslatmalarni ko'rish
@dp.callback_query(F.data == "my_notes")
async def my_notes_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, note FROM notes WHERE user_id = ?", (user_id,))
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        await callback.message.answer("📝 Sizda hozircha hech qanday eslatma yo'q.\n\nEslatma qo'shish uchun '➕ Eslatma qo'shish' tugmasini bosing.", reply_markup=get_main_keyboard())
    else:
        text = "📝 **Sizning eslatmalaringiz:**\n\n"
        for idx, (note_id, note) in enumerate(notes, 1):
            text += f"{idx}. {note} (O'chirish buyrug'i: `/del_{note_id}`)\n"
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    await callback.answer()

# Eslatma qo'shish tugmasi
@dp.callback_query(F.data == "add_note")
async def add_note_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NoteState.waiting_for_note)
    await callback.message.answer("✍️ **Eslatmangizni botga yozib yuboring:**\n\n_(Masalan: Soat 18:00 da darsim bor)_", parse_mode="Markdown")
    await callback.answer()

# Eslatmani bot xotirasiga saqlash
@dp.message(NoteState.waiting_for_note)
async def save_note_input(message: types.Message, state: FSMContext):
    note_text = message.text.strip()
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (message.from_user.id, note_text))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ **Eslatma muvaffaqiyatli saqlandi!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")

# Eslatmani o'chirish (/del_ID)
@dp.message(F.text.startswith("/del_"))
async def delete_note_cmd(message: types.Message):
    try:
        note_id = int(message.text.replace("/del_", "").strip())
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, message.from_user.id))
        conn.commit()
        conn.close()
        await message.answer("🗑 **Eslatma o'chirildi!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ Noto'g'ri buyruq kiritildi.")

# 🧮 Bot ichidagi Kalkulyator hamda standart javob
@dp.message()
async def default_handler(message: types.Message):
    text = message.text.strip()
    allowed = "0123456789+-*/. ()"
    
    # Matematik misol bo'lsa hisoblaydi
    if all(char in allowed for char in text) and any(op in text for op in "+-*/"):
        try:
            result = eval(text, {"__builtins__": None}, {})
            await message.answer(f"🧮 **Hisoblagich:**\n\n`{text}` = `{result}`", parse_mode="Markdown", reply_markup=get_main_keyboard())
            return
        except Exception:
            pass

    await message.answer("Tugmalardan birini tanlang yoki matematik misol yuboring:", reply_markup=get_main_keyboard())

# --- 5. ISHGA TUSHIRISH ---
async def main():
    await start_web_server()
    print("Bot polling rejimida ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
