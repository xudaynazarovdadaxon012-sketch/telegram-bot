import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    WebAppInfo, 
    LabeledPrice, 
    PreCheckoutQuery
)

# ---------------------------------------------------------
# CONFIGURE & ENVIRONMENT
# ---------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------------------------------------------------------
# 1. DATABASE INITIALIZATION (SQL)
# ---------------------------------------------------------
async def init_db():
    async with aiosqlite.connect("database.db") as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 100,
                is_vip INTEGER DEFAULT 0,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # To'lovlar tarixi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                service_type TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ---------------------------------------------------------
# 2. START & MAIN MENU
# ---------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None

    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_exists = await cursor.fetchone()

        if not user_exists:
            await db.execute(
                "INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, referrer_id)
            )
            if referrer_id:
                await db.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (referrer_id,))
            await db.commit()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Launch Mega WebApp & 3D Game", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Get VIP Pass (50 Stars)", callback_data="buy_vip")],
            [InlineKeyboardButton(text="🔗 Referal Havola", callback_data="ref_link")]
        ]
    )
    
    await message.answer(
        f"⚡ **Mega Utility & Cyber Studio Hub**\n\n"
        f"Xush kelibsiz, **{message.from_user.first_name}**!\n"
        f"3D o'yin, analitika va barcha utilitlar ishga tayyor.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# 3. REFERAL TIZIMI
# ---------------------------------------------------------
@dp.callback_query(F.data == "ref_link")
async def send_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    await callback.message.answer(
        f"🚀 **Sizning referal havolangiz:**\n`{ref_link}`\n\n"
        f"Do'stlaringizni taklif qiling va har bir do'stingiz uchun **500 Tanga** oling!",
        parse_mode="Markdown"
    )
    await callback.answer()

# ---------------------------------------------------------
# 4. MONETIZATION (TELEGRAM STARS & VIP PASS)
# ---------------------------------------------------------
@dp.callback_query(F.data == "buy_vip")
async def send_vip_invoice(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="VIP Lifetime Access", amount=50)] # 50 Stars
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Status Access",
        description="3D o'yinda premium imkoniyatlar va cheksiz analitikani ochish.",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="buy-vip-access",
        payload="vip_subscription"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    
    async with aiosqlite.connect("database.db") as db:
        await db.execute("UPDATE users SET is_vip = 1, coins = coins + 2000 WHERE user_id = ?", (user_id,))
        await db.execute("INSERT INTO payments (user_id, amount, service_type, status) VALUES (?, ?, ?, ?)", 
                         (user_id, 50, "VIP_PASS", "SUCCESS"))
        await db.commit()

    await message.answer("🎉 Tabriklaymiz! Siz VIP maqomini qo'lga kiritdingiz!")

# ---------------------------------------------------------
# 5. WHITELABEL ADMIN CONTROL PANEL
# ---------------------------------------------------------
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1") as c2:
            vip_users = (await c2.fetchone())[0]
        async with db.execute("SELECT SUM(amount) FROM payments WHERE status='SUCCESS'") as c3:
            total_revenue = (await c3.fetchone())[0] or 0

    await message.answer(
        f"⚙️ **Whitelabel Admin Control Panel**\n\n"
        f"👥 Jami foydalanuvchilar: **{total_users} ta**\n"
        f"👑 VIP a'zolar: **{vip_users} ta**\n"
        f"💰 Umumiy tushum: **{total_revenue} Telegram Stars**\n"
        f"🗄️ Baza: **SQLite Active**",
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# 6. RUNNER
# ---------------------------------------------------------
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
