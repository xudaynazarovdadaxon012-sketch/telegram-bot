import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BOT_TOKEN = "8760162640:AAECQSshZ5jA3goZUWx4rG8MIfLkrBrRk20"  # Bu yerga yangi tokeningizni qo'ying

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class TaskState(StatesGroup):
    waiting_for_task = State()
    waiting_for_time = State()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Vazifa qo'shish")],
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Xush kelibsiz! Vazifalaringiz va eslatmalaringizni boshqaruvchi botga hush kelibsiz.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "➕ Vazifa qo'shish")
async def add_task_start(message: types.Message, state: FSMContext):
    await message.answer("Vazifa nomini kiriting:")
    await state.set_state(TaskState.waiting_for_task)

@dp.message(TaskState.waiting_for_task)
async def process_task_name(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("Necha soniyadan keyin eslatay? (Masalan: 10)")
    await state.set_state(TaskState.waiting_for_time)

async def send_reminder(chat_id: int, task_name: str, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.send_message(chat_id, f"⏰ **ESLATMA!**\n\nVazifa: {task_name}")
    except Exception as e:
        print(f"Xatolik: {e}")

@dp.message(TaskState.waiting_for_time)
async def process_task_time(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 10)!")
        return
    
    seconds = int(message.text)
    user_data = await state.get_data()
    task_name = user_data.get("task_name")
    
    await message.answer(f"✅ Vazifa saqlandi! {seconds} soniyadan keyin eslataman.")
    await state.clear()
    
    # Eslatmani orqa fonda (background task) yuritish
    asyncio.create_task(send_reminder(message.chat.id, task_name, seconds))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
