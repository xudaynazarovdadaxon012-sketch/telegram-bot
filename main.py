import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# .env faylidan tokenni yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot va Dispatcher obyektlarini yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start buyrug'i uchun
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Xush kelibsiz! Eslatma o'rnatish uchun:\n`/eslat HH:MM [matn]` shaklida yuboring.")

# /eslat buyrug'i uchun
@dp.message(Command("eslat"))
async def set_reminder(message: types.Message):
    try:
        args = message.text.split(maxsplit=2)
        time_str = args[1]
        text = args[2]

        now = datetime.now()
        target_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )

        if target_time < now:
            target_time = target_time.replace(day=now.day + 1)

        wait_seconds = (target_time - now).total_seconds()

        await message.answer(f"⏳ **Eslatma oʻrnatildi!**\nSoat **{time_str}** da sizga xabar yuboraman.")

        await asyncio.sleep(wait_seconds)

        await message.answer(f"🔔 **ESLATMA!**\n\n📌 *{text}*")

    except (IndexError, ValueError):
        await message.answer(
            "⚠️ **Toʻgʻri formatda kiriting:**\n"
            "`/eslat HH:MM [eslatma matni]`\n\n"
            "**Misol:** `/eslat 18:30 Mini App o'yinini tekshirish`"
        )

# Botni ishga tushirish funksiyasi
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
