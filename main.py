import os
import sqlite3
import logging
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, PreCheckoutQuery, ContentType, LabeledPrice
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# Token Environment Variable orqali xavfsiz olinadi
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ==================== 1. DATABASE SETUP ====================
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

def get_user_data(user_id: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, username, balance, coins, is_vip FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "full_name": row[1],
            "username": row[2],
            "balance": row[3],
            "coins": row[4],
            "is_vip": bool(row[5])
        }
    return None

def register_or_update_user(user_id: int, full_name: str, username: str):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, full_name, username, balance, coins, is_vip) VALUES (?, ?, ?, 0.0, 0, 0)",
            (user_id, full_name, username)
        )
    else:
        cursor.execute(
            "UPDATE users SET full_name = ?, username = ? WHERE user_id = ?",
            (full_name, username, user_id)
        )
    conn.commit()
    conn.close()

def set_user_vip(user_id: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ==================== 2. BOT HANDLERS ====================
@router.message(CommandStart())
async def cmd_start(message: Message):
    register_or_update_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or ""
    )
    user_data = get_user_data(message.from_user.id)
    
    vip_status = "⭐ VIP A'zo (2x Bonus)" if user_data["is_vip"] else "Oddiy foydalanuvchi"
    
    await message.answer(
        f"Xush kelibsiz, {user_data['full_name']}!\n\n"
        f"📌 Status: {vip_status}\n"
        f"💰 Balans: {user_data['balance']} UZS\n"
        f"🪙 Tangalar: {user_data['coins']} coin\n\n"
        f"VIP darajasiga o'tish va 2x bonus olish uchun /buy_vip buyrug'ini yuboring."
    )

@router.message(F.text == "/buy_vip")
async def process_buy_vip(message: Message):
    prices = [LabeledPrice(label="VIP Obuna (1 oy)", amount=100)]  # 100 Telegram Stars
    await message.answer_invoice(
        title="VIP Status Sotib Olish",
        description="VIP maqomiga ega bo'ling va 2x bonus hamda maxsus imkoniyatlarni qo'lga kiriting!",
        payload="vip_subscription_payload",
        currency="XTR",
        prices=prices
    )

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    if message.successful_payment.invoice_payload == "vip_subscription_payload":
        set_user_vip(message.from_user.id)
        await message.answer("🎉 Tabriklaymiz! Siz muvaffaqiyatli VIP statusiga ega bo'ldingiz!")

# ==================== 3. RENDER PORT DUMMY SERVER ====================
async def handle(request):
    return web.Response(text="Bot Web Service Active")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ==================== 4. MAIN ENTRYPOINT ====================
async def main():
    init_db()
    asyncio.create_task(start_dummy_server())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
