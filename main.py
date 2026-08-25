import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '8760162640:AAECQSshZ5jA3goZUWx4rG8MIfLkrBrRk20'  # BotFather'dan olingan token

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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
        now = datetime.now()
        target_time = datetime.strptime(user_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        
        delay = (target_time - now).total_seconds()
        if delay < 0:
            delay += 86400  # Agar ko'rsatilgan vaqt o'tib ketgan bo'lsa, ertangi kunga o'tkazadi

        data = await state.get_data()
        reminder_text = data.get('text')
        await state.clear()
        
        await message.answer(f"Kelishdik! Eslatma {user_time_str} ga o'rnatildi.")
        
        await asyncio.sleep(delay)
        await message.answer(f"🔔 **Eslatma:** {reminder_text}")
        
    except ValueError:
        await message.answer("Vaqt formati noto'g'ri. Iltimos, **HH:MM** ko'rinishida kiriting (masalan: 09:15 yoki 18:30).")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
