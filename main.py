import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, WebAppInfo

BOT_TOKEN = "8760162640:AAExYGsmAdvlR4t9VQ61XVEQgNxjc2FpPAA"
MINI_APP_URL = "https://telegram-bot-7n6t.onrender.com"  # Render'dagi HTML havola
SPONSOR_CHANNEL = "@your_channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Narxlar (Telegram Stars)
PRICES = {
    "day": 15,
    "month": 99,
    "year": 699
}

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Mini App (Games Hub)", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="⚡ PRO Obuna (Stars)", callback_data="open_pro")],
        [InlineKeyboardButton(text="📢 Homiy Kanal", url=f"https://t.me/{SPONSOR_CHANNEL[1:]}")]
    ])

def pro_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Kunlik — 15 ⭐", callback_data="buy_day")],
        [InlineKeyboardButton(text="1 Oylik — 99 ⭐ (TOP)", callback_data="buy_month")],
        [InlineKeyboardButton(text="1 Yillik — 699 ⭐", callback_data="buy_year")]
    ])

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Xush kelibsiz! Mini App va PRO imkoniyatlardan foydalanishingiz mumkin:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "open_pro")
async def show_pro(callback: types.CallbackQuery):
    await callback.message.answer(
        "💎 **PRO Obuna imkoniyatlari:**\n"
        "• Cheksiz AI Chat va HD Rasm Yaratish\n"
        "• 4K Video Yuklash va Tezkor Ishlov\n"
        "• Reklamasiz foydalanish\n\n"
        "Tarifni tanlang:",
        parse_mode="Markdown",
        reply_markup=pro_menu()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def process_payment(callback: types.CallbackQuery):
    plan = callback.data.split("_")[1]
    if plan in PRICES:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"PRO {plan.capitalize()} Obuna",
            description=f"Botdagi cheksiz PRO imkoniyatlarni {plan} muddatga faollashtirish.",
            payload=f"pro_subscription_{plan}_{callback.from_user.id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=f"PRO {plan}", amount=PRICES[plan])]
        )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_query: PreCheckoutQuery):
    # To'lov tayyorgarligini tasdiqlash
    await bot.answer_pre_checkout_query(pre_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    payload = message.successful_payment.invoice_payload
    await message.answer("🎉 Tabriklaymiz! To'lov muvaffaqiyatli amalga oshirildi va PRO status faollashtirildi.")

# WebApp'dan kelgan ma'lumotlarni qabul qilish
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    data = message.web_app_data.data
    if data == "open_pro":
        await message.answer("💎 PRO bo'limi:", reply_markup=pro_menu())
    else:
        await message.answer(f"Natija: {data}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
