import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# BotFather'dan olingan tokenni shu yerga joylang
BOT_TOKEN = "8760162640:AAECQSshZ5jA3goZUWx4rG8MIfLkrBrRk20"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

# Tugmalar menyusi
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Vazifa qo'shish")]
    ],
    resize_keyboard=True
)

# Ma'lumotlarni bosqichma-bosqich yig'ish holatlari
class TaskState(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

# /start buyrug'i uchun
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "Assalomu alaykum! Men sizga vazifalaringizni eslatib turuvchi botman.",
        reply_markup=main_keyboard
    )

# Vazifa qo'shish tugmasi bosilganda
@dp.message(F.text == "➕ Vazifa qo'shish")
async def add_task_start(message: Message, state: FSMContext):
    await message.answer("Vazifa matnini kiriting (masalan: Dars qilish):")
    await state.set_state(TaskState.waiting_for_text)

# Vazifa matni qabul qilinganda
@dp.message(TaskState.waiting_for_text)
async def process_task_text(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer(
        "Eslatma vaqtini quyidagi formatda kiriting:\n"
        "**YYYY-MM-DD HH:MM**\n\n"
        "Masalan: `2026-08-25 18:30`",
        parse_mode="Markdown"
    )
    await state.set_state(TaskState.waiting_for_time)

# Eslatma yuboradigan funksiya
async def send_reminder(chat_id: int, text: str):
    await bot.send_message(chat_id, f"🔔 **ESLATMA!**\n\nVazifa vaqti keldi:\n👉 **{text}**", parse_mode="Markdown")

# Vaqt qabul qilinganda va taymerga qo'shilganda
@dp.message(TaskState.waiting_for_time)
async def process_task_time(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task_text = user_data['task_text']
    
    try:
        # Vaqtni format bo'yicha tekshirish
        run_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        
        if run_time <= datetime.now():
            await message.answer("⚠️ O'tib ketgan vaqtni kiritdingiz! Kelajakdagi vaqtni kiriting.")
            return

        # Taymerga qo'shish (APScheduler)
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=run_time,
            args=[message.chat.id, task_text]
        )

        await message.answer(
            f"✅ Eslatmalaringiz saqlandi!\n\n"
            f"📌 **Vazifa:** {task_text}\n"
            f"⏰ **Vaqti:** {message.text}",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
        await state.clear()

    except ValueError:
        await message.answer("❌ Vaqt formati noto'g'ri kiritildi! Iltimos, `2026-08-25 18:30` ko'rinishida yozing.")

import asyncio
import os
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def main():
    scheduler.start()
    
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
