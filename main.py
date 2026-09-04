import os
from aiohttp import web
import logging
import sqlite3
import json
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, PreCheckoutQuery, ContentType, LabeledPrice
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# 1. SQLite Baza Initsializatsiyasi
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0,
            coins INTEGER DEFAULT 0,
            is_vip INTEGER DEFAULT 0,
            vip_expires_at TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

# User ma'lumotlarini olish
def get_user_data(user_id: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, coins, is_vip FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"balance": res[0], "coins": res[1], "is_vip": bool(res[2])}
    return {"balance": 0.0, "coins": 0, "is_vip": False}

# VIP statusni yangilash
def activate_vip(user_id: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# 2. Start buyrug'i va Userni bazaga yozish
@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, full_name, username) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET full_name=?, username=?
    """, (user.id, user.full_name, user.username, user.full_name, user.username))
    conn.commit()
    conn.close()
    
    await message.answer(f"Xush kelibsiz, {user.first_name}! Mini App-ni ochish uchun pastdagi tugmani bosing.")

# 3. Telegram Stars VIP Obuna To'lovi
@router.message(F.text == "/buy_vip")
async def send_vip_invoice(message: Message):
    prices = [LabeledPrice(label="VIP Status (1 Oy)", amount=250)] # 250 Telegram Stars
    await message.answer_invoice(
        title="VIP Obuna 👑",
        description="VIP status: 2x bonuslar, eksklyuziv o'yinlar va oltin nishon!",
        payload="vip_subscription_payload",
        currency="XTR",
        prices=prices
    )

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    if message.successful_payment.invoice_payload == "vip_subscription_payload":
        activate_vip(message.from_user.id)
        await message.answer("Siz muvaffaqiyatli VIP statusga ega bo'ldingiz! 👑 Mini App-ni qayta oching.")

# 4. Mini App API Data Handler
@router.message(F.web_app_data)
async def web_app_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "get_user_info":
            user_info = get_user_data(message.from_user.id)
            await message.answer(
                f"📊 <b>Hisobingiz:</b>\n"
                f"💳 Balans: ${user_info['balance']:.2f}\n"
                f"🪙 Coins: {user_info['coins']}\n"
                f"👑 VIP Status: {'Aktiv 👑' if user_info['is_vip'] else 'Yoqilmagan'}",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    init_db()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
