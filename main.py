import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# BotFather'dan olgan YANGI tokeningizni qo'ying (eski tokeningiz o'chirilgani uchun)
BOT_TOKEN = "8760162640:AAFJ3U60hJC3XzpQb2IJYTCy23qmtuiv79M"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start buyrug'i (Mini App tugmasi bilan)
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Mini App tugmasini yaratish
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ob-havo Mini App ⛅",
                    web_app=WebAppInfo(url="https://sizning-miniapp-saytingiz.vercel.app")  # HTML saytingiz havolasi
                )
            ]
        ]
    )

    await message.answer(
        "Assalomu alaykum! Eslatma o'rnatish uchun buyruqni quyidagicha yuboring:\n\n"
        "`/eslat HH:MM [matn]`\n\n"
        "**Misol:** `/eslat 18:30 Dars qilish`\n\n"
        "Ob-havoni ko'rish uchun pastdagi tugmani bosing:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# /eslat buyrug'i (eslatma o'rnatish logikasi)
@dp.message(Command("eslat"))
async def set_reminder(message: types.Message):
    try:
        args = message.text.split(maxsplit=2)
        time_str = args[1]
        text = args[2]
        
        await message.answer(f"Eslatma saqlandi: {time_str} da '{text}' haqida eslataman.")
    except Exception:
        await message.answer("Xatolik! Format: `/eslat 18:30 Dars qilish`", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
