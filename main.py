import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from database import init_db, get_or_create_user, claim_daily_streak

# Server muhitidan o'zgaruvchilarni olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://xudaynazarovdadaxon012-sketch.github.io/telegram-bot/") # GitHub Pages linki

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bazani ishga tushirish
init_db()

async def check_subscription(user_id: int) -> bool:
    """Homiy kanalga a'zolikni tekshirish (Kanal bo'lmasa avtomatik o'tkazadi)"""
    if not SPONSOR_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Referal ID ni aniqlash (/start 1234567)
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    user = get_or_create_user(user_id, referrer_id)
    
    # Kanalga a'zolikni tekshirish
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        channel_link = SPONSOR_CHANNEL.replace('@', '')
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{channel_link}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ])
        await message.answer("⚠️ Botdan foydalanish uchun homiy kanalimizga a'zo bo'ling:", reply_markup=kb)
        return

    # Asosiy tugmalar (Web App bilan)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Cyber Hub (Mini App)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🎁 Kunlik Bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="⭐ VIP Sotib Olish (Stars)", callback_data="buy_stars")]
    ])
    
    await message.answer(
        f"👋 Salom, {message.from_user.first_name}!\n\n"
        f"💰 Balansingiz: **{user[1]} Coins**\n"
        f"👥 Taklif qilgan do'stlaringiz: **{user[2]} ta**\n\n"
        f"Pastdagi tugma orqali Mini App-ni oching:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

# Kunlik bonus callback
@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_handler(callback: types.CallbackQuery):
    status, streak, reward = claim_daily_streak(callback.from_user.id)
    if status:
        await callback.answer(f"🎉 Tabriklaymiz! {streak}-kunlik bonus: +{reward} Coins!", show_alert=True)
    else:
        await callback.answer("⚠️ Siz bugungi bonusni olib bo'lgansiz. Ertaga qayta kiring!", show_alert=True)

# Telegram Stars To'lovi (In-App Purchase)
@dp.callback_query(F.data == "buy_stars")
async def send_invoice(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="VIP Maqom", amount=50)] # 50 Telegram Stars
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Maqom xaridi",
        description="Botda reklamasiz rejim va eksklyuziv imkoniyatlarni yoqish.",
        payload="vip_status_pack",
        currency="XTR", # Telegram Stars valyutasi kodi
        prices=prices
    )

# Stars to'lovi so'rovini tasdiqlash (Pre-checkout)
@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# To'lov muvaffaqiyatli amalga oshganda
@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    await message.answer("🎉 To'lov muvaffaqiyatli amalga oshirildi! VIP maqomingiz faollashtirildi.")
