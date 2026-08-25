import os
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot alive"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Telegram Bot Token
API_TOKEN = '8760162640:AAGhmn9AtwtXIvk234ETV-gKA6aeCQKDPnY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
UZB_TZ = timezone(timedelta(hours=5))

# Ma'lumotlar bazasini sozlash (SQLite)
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            remind_time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Form(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

# Asosiy menyu tugmalari
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi eslatma", callback_data="add_reminder")],
        [InlineKeyboardButton(text="📋 Eslatmalarim", callback_data="list_reminders")],
        [InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="about")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"👋 Salom, **{message.from_user.first_name}**!\n\n"
        "Men sizning shaxsiy rejalashtiruvchi yordamchingizman. Quyidagi tugmalardan birini tanlang:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤖 **Pro Rejalashtiruvchi Bot**\n\n"
        "Ushbu bot sizga muhim topshiriqlar va uchrashuvlarni o'z vaqtida eslatib turadi.",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "add_reminder")
async def add_reminder_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Nima haqida eslatishim kerak? Matnni kiriting:")
    await state.set_state(Form.waiting_for_text)

@dp.message(Form.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("⏰ Soat nechada eslatay? (Format: **HH:MM**, masalan: 14:30):")
    await state.set_state(Form.waiting_for_time)

@dp.message(Form.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    user_time_str = message.text.strip()
    try:
        now = datetime.now(UZB_TZ)
        parsed_time = datetime.strptime(user_time_str, "%H:%M").time()
        target_time = datetime.combine(now.date(), parsed_time).replace(tzinfo=UZB_TZ)
        
        if target_time <= now:
            target_time += timedelta(days=1)
            
        delay = (target_time - now).total_seconds()
        data = await state.get_data()
        reminder_text = data.get('text')
        
        # Bazasiga saqlash
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (user_id, text, remind_time) VALUES (?, ?, ?)", 
                       (message.from_user.id, reminder_text, target_time.strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        await state.clear()
        await message.answer(
            f"✅ **Eslatma saqlandi!**\n\n📌 **Matn:** {reminder_text}\n🕒 **Vaqt:** {user_time_str}",
            reply_markup=main_menu()
        )
        
        await asyncio.sleep(delay)
        await message.answer(f"🔔 **ESLATMA!**\n\n📌 {reminder_text}")
        
    except ValueError:
        await message.answer("❌ Noto'g'ri vaqt kiritildi. Iltimos, **HH:MM** formatida yozing (masalan: 09:15).")

@dp.callback_query(F.data == "list_reminders")
async def list_reminders(callback: types.CallbackQuery):
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text, remind_time FROM reminders WHERE user_id = ?", (callback.from_user.id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        text = "📭 Sizda hozircha faol eslatmalar yo'q."
    else:
        text = "📋 **Sizning eslatmalaringiz:**\n\n"
        for i, row in enumerate(rows, 1):
            text += f"{i}. {row[0]} — 🕒 {row[1]}\n"

    await callback.message.edit_text(text, reply_markup=main_menu())

# Render o'chib qolmasligi uchun veb-server
async def handle(request):
    return web.Response(text="Bot faol ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
  asyncio.run(main())a bor bo'lgan kodi
