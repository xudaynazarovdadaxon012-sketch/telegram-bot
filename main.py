import asyncio
import os
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

API_TOKEN = '8760162640:AAGhmn9AtwtXIvk234ETV-gKA6aeCQKDPnY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

UZB_TZ = timezone(timedelta(hours=5))

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
            
        delay = (target_time - now).total_seconds()

        data = await state.get_data()
        reminder_text = data.get('text')
        await state.clear()
        
        await message.answer(f"Kelishdik! O'zbekiston vaqti bilan {user_time_str} ga o'rnatildi.")
        
        # Eslatmani kutish
        await asyncio.sleep(delay)
        await message.answer(f"🔔 **Eslatma:** {reminder_text}")
        
    except ValueError:
        await message.answer("Vaqt formati noto'g'ri. Iltimos, **HH:MM** ko'rinishida kiriting (masalan: 09:15 yoki 18:30).")

# Render port talab qilgani uchun soxta veb-server
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Veb serverni va botni bir vaqtda ishga tushirish
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
