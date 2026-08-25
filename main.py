import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '8760162640:AAECQSshZSJA3goZUWx4rG8MIFLkrBrRk20'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# O'zbekiston vaqt mintaqasi (UTC+5)
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
        # Hozirgi O'zbekiston vaqti
        now = datetime.now(UZB_TZ)
        
        # Foydalanuvchi kiritgan vaqt
        parsed_time = datetime.strptime(user_time_str, "%H:%M").time()
        
        # Bugungi shu soat (O'zbekiston vaqti bilan)
        target_time = datetime.combine(now.date(), parsed_time).replace(tzinfo=UZB_TZ)
        
        # Agar vaqt o'tib ketgan bo'lsa, ertangi kunga o'tkazadi
        if target_time <= now:
            target_time += timedelta(days=1)
            
        delay = (target_time - now).total_seconds()

        data = await state.get_data()
        reminder_text = data.get('text')
        await state.clear()
        
        await message.answer(f"Kelishdik! Eslatma O'zbekiston vaqti bilan {user_time_str} ga o'rnatildi.")
        
        await asyncio.sleep(delay)
        await message.answer(f"🔔 **Eslatma:** {reminder_text}")
        
    except ValueError:
        await message.answer("Vaqt formati noto'g'ri. Iltimos, **HH:MM** ko'rinishida kiriting (masalan: 09:15 yoki 18:30).")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
