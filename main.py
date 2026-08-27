import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Bot tokeningizni kiriting
BOT_TOKEN = "8760162640:AAFJ3U60hJC3XzpQb2IJYTCy23qmtuiv79M"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# /start buyrug'i uchun handler (Mini App tugmasisiz)
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Eslatma o'rnatish uchun buyruqni quyidagicha yuboring:\n\n"
        "<code>/eslat HH:MM [matn]</code>\n\n"
        "Misol: <code>/eslat 18:30 Dars qilish</code>",
        parse_mode="HTML"
    )

# Oddiy matnli xabarlar uchun handler
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(
        "Eslatma o'rnatish uchun /start buyrug'ini yuboring."
    )

if __name__ == "__main__":
    dp.run_polling(bot)
