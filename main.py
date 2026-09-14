import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import LabeledPrice, PreCheckoutQuery

# Tokenlarni o'rnating
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = ""  # Telegram Stars uchun provider token shart emas (bo'sh qoldiriladi)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Har bir foydalanuvchi uchun ma'lumotlar bazasi o'rnini bosuvchi oddiy lug'at
user_data = {}

REQUIRED_CHANNELS = [
    "@kanal_1",
    "@kanal_2",
    "@kanal_3",
    "@kanal_4",
    "@kanal_5"
]

# Obunani tekshirish funksiyasi
async def check_subscriptions(user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Foydalanuvchi bazada bormi tekshiramiz
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "tap_power": 1}

    # Kanallarga obunani tekshiramiz
    is_subscribed = await check_subscriptions(user_id)
    
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in REQUIRED_CHANNELS])
        await message.answer(
            f"O'yinni boshlash uchun quyidagi 5 ta homiy kanalga a'zo bo'ling:\n\n{channels_text}\n\n"
            f"A'zo bo'lgach, /start buyrug'ini qaytadan bosing."
        )
        return

    # Agar obuna bo'lgan bo'lsa, o'yin menyusini ko'rsatamiz
    kb = [
        [types.KeyboardButton(text="🪙 Tap qilish")],
        [types.KeyboardButton(text="⭐ Tap quvvatini oshirish (10 Stars)")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    bal = user_data[user_id]["balance"]
    power = user_data[user_id]["tap_power"]
    
    await message.answer(
        f"Xush kelibsiz!\n\nBalansingiz: {bal} tanga\nTap quvvati: {power}x\n\nPastdagi tugmani bosing:",
        reply_markup=keyboard
    )

@dp.message(F.text == "🪙 Tap qilish")
async def tap_action(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "tap_power": 1}
    
    power = user_data[user_id]["tap_power"]
    user_data[user_id]["balance"] += power
    
    bal = user_data[user_id]["balance"]
    await message.answer(f"+{power} tanga! 🪙 Jami: {bal} tanga")

@dp.message(F.text == "⭐ Tap quvvatini oshirish (10 Stars)")
async def buy_boost(message: types.Message):
    # Telegram Stars orqali to'lov yaratish
    prices = [LabeledPrice(label="Tap quvvatini 2x qilish", amount=10)] # 10 Stars (valyuta 'XTR' da narx miqdori o'zi yulduzlarni bildiradi)
    
    await message.answer_invoice(
        title="Tap Quvvatini Oshirish",
        description="Har bir tap uchun beriladigan tangalar miqdorini 2 barobarga oshiring!",
        prices=prices,
        payload="boost_tap_power",
        currency="XTR", # Telegram Stars valyuta kodi
    )

# Pre-checkout (To'lovdan oldingi tasdiq)
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# To'lov muvaffaqiyatli yakunlanganda
@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]["tap_power"] = 2  # Tap quvvatini 2 ga chiqaramiz
        
    await message.answer("Tabriklaymiz! To'lov muvaffaqiyatli amalga oshirildi. Endi har bir tap uchun 2 tadan tanga beriladi! 🎉")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
