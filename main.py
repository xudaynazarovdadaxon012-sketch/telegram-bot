import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = '8760162640:AAECQSshZSJA3goZUWx4rG8MIFLkrBrRk20'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

UZB_TZ = timezone(timedelta(hours=5))

# SQLite Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            text TEXT,
            remind_time TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_reminder(chat_id, text, remind_time):
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)",
                   (chat_id, text, remind_time.isoformat()))
    conn.commit()
    conn.close()

# Har 30 soniyada vaqti kelgan eslatmalarni tekshiradigan funksiya
async def check_reminders():
    now = datetime.now(UZB_TZ)
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, chat_id, text, remind_time FROM reminders")
    rows = cursor.fetchall()
    
    for row in rows:
        rem_id, chat_id, text, remind_time_str = row
        remind_time = datetime.fromisoformat(remind_time_str)
        
        if now >= remind_time:
            try:
                await bot.send_message(chat_id, f"🔔 **Eslatma:** {text}")
            except Exception as e:
                print(f"Xatolik: {e}")
            cursor.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
            conn.commit()
            
    conn.close()

class Form(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Eslatma qo'shish uchun /remind buyrug'ini yuboring.")

@dp.message(Command("remind"))
async def remind_handler(message: types.Message, state: FSMContext):
    await message.answer("Nima haqida eslatib o'tay?")
    await state.set_state(Form.waiting_for_text)

@dp.message(Form.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Soat nechada eslatay? (Format: HH:MM, masalan 14:30)")
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

        data = await state.get_data()
        reminder_text = data.get('text')
        
        save_reminder(message.chat.id, reminder_text, target_time)
        await state.clear()
        
        await message.answer(f"Kelishdik! Eslatma {user_time_str} ga saqlandi.")
        
    except ValueError:
        await message.answer("Vaqt formati noto'g'ri. Iltimos, **HH:MM** ko'rinishida kiriting (masalan: 09:15 yoki 18:30).")

async def main():
    init_db()
    scheduler.add_job(check_reminders, 'interval', seconds=30)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
