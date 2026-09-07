import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
    WebAppInfo,
)


# GitHub'da token ko'rinmaydi, xavfsiz!
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Vercel yoki Netlify'dan olgan HTTPS linkingiz
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# /start buyrug'i kelganda Mini App tugmasini yuborish
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Mega App & 3D Game-ni ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}!\n\n"
        f"Barcha ai-xizmatlar va Sky Jumper 3D o'yinidan foydalanish uchun pastdagi tugmani bosing:",
        reply_markup=kb,
    )


# Telegram Stars to'lovini qabul qilish (In-App Purchase)
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# To'lov muvaffaqiyatli amalga oshganda
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await message.answer(
        f"🎉 To'lov muvaffaqiyatli amalga oshirildi!\n"
        f"Xarid qilingan stars: {message.successful_payment.total_amount}\n"
        f"Rahmat!"
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
