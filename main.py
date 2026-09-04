import os
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8898979946))

# Homiy kanal (Majburiy a'zolik uchun)
SPONSOR_CHANNEL = "@your_channel_username" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

def init_db():
    conn = sqlite3.connect("platform_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            stars_balance INTEGER DEFAULT 0,
            free_daily_limits INTEGER DEFAULT 5,
            is_vip INTEGER DEFAULT 0,
            vip_expire TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Homiy kanalga a'zolikni tekshirish (1-daromad manbai)
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True  # Kanal sozlanmagan bo'lsa o'tkazib yuboradi

@router.message(CommandStart())
async def cmd_start(message: Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            f"⚠️ **Xizmatdan foydalanish uchun homiy kanalimizga a'zo bo'ling:**\n\n"
            f"👉 {SPONSOR_CHANNEL}\n\n"
            f"A'zo bo'lib, qayta /start bosing."
        )
        return

    await message.answer(
        "✨ **Prime Elite Mini App'ga xush kelibsiz!**\n\n"
        "🎁 Kunlik 5 ta bepul AI so'rovingiz mavjud.\n"
        "👑 Cheksiz foydalanish uchun **VIP Pass** yoki **Telegram Stars** xarid qilishingiz mumkin."
    )

# Telegram Stars To'lovi (2-daromad manbai)
@router.message(F.text == "/buy_stars")
async def send_stars_invoice(message: Message):
    prices = [LabeledPrice(label="50 AI Stars Pack", amount=50)]  # 50 Telegram Stars
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="50 AI Stars To'plami",
        description="Mini App ichida eksklyuziv AI va media xizmatlaridan foydalanish uchun.",
        payload="stars_pack_50",
        provider_token="",  # Telegram Stars uchun bo'sh qoladi
        currency="XTR",
        prices=prices
    )

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    # To'lov muvaffaqiyatli amalga oshganda balansni to'ldirish
    conn = sqlite3.connect("platform_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET stars_balance = stars_balance + 50 WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    conn.close()
    
    await message.answer("🎉 To'lov muvaffaqiyatli amalga oshirildi! 50 Stars balansingizga qo'shildi.")

async def start_web_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    asyncio.create_task(start_web_server())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
