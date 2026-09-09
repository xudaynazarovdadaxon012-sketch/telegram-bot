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

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------------------------------------------------------
# 1. BAZA VA JADVALLARNI INITIALIZATSIYA QILISH (SQL)
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
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tranzaksiyalar jadvali (To'lovlar uchun)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ---------------------------------------------------------
# 2. LOGIKA VA BUYRUG'LAR
# ---------------------------------------------------------

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    # Referal ID ni aniqlash (/start 123456 formatida kelganda)
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None

    async with aiosqlite.connect("database.db") as db:
        # Foydalanuvchi bor-yo'qligini tekshirish
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_exists = await cursor.fetchone()

        if not user_exists:
            # Yangi foydalanuvchini saqlash
            await db.execute(
                "INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, referrer_id)
            )
            # Agar referal orqali kirgan bo'lsa, taklif qilganga 500 coin mukofot berish
            if referrer_id:
                await db.execute(
                    "UPDATE users SET coins = coins + 500 WHERE user_id = ?",
                    (referrer_id,)
                )
            await db.commit()

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Launch Studio & 3D Game", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Buy Cyber Coins (Stars)", callback_data="buy_coins")],
            [InlineKeyboardButton(text="🔗 Taklifnoma havolasi", callback_data="ref_link")]
        ]
    )
    
    await message.answer(
        f"🤖 **Mega Utility & Cyber Studio Hub**\n\n"
        f"Xush kelibsiz, {message.from_user.first_name}!\n"
        f"O'yin va barcha analitik vositalar ishga tayyor.",
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
        f"Do'stlaringizni taklif qiling va har bir do'stingiz uchun **500 Cyber Coin** oling!",
        parse_mode="Markdown"
    )
    await callback.answer()

# ---------------------------------------------------------
# 4. TELEGRAM STARS MONETIZATSIYA (TO'LOV TIZIMI)
# ---------------------------------------------------------
@dp.callback_query(F.data == "buy_coins")
async def send_invoice(callback: types.CallbackQuery):
    # 50 Telegram Stars evaziga 1000 Coins sotish
    prices = [LabeledPrice(label="1000 Cyber Coins", amount=50)]
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="1000 Cyber Coins",
        description="3D o'yinda va premium vositalarda ishlatish uchun tangalar paketini xarid qiling.",
        provider_token="",  # Telegram Stars uchun bo'sh qoladi
        currency="XTR",     # Telegram Stars valyutasi
        prices=prices,
        start_parameter="buy-coins-pack",
        payload="coins_pack_1000"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    
    async with aiosqlite.connect("database.db") as db:
        # Balansni yangilash
        await db.execute("UPDATE users SET coins = coins + 1000 WHERE user_id = ?", (user_id,))
        # Tranzaksiyani saqlash
        await db.execute("INSERT INTO payments (user_id, amount, status) VALUES (?, ?, ?)", (user_id, 50, "SUCCESS"))
        await db.commit()

    await message.answer("🎉 Xarid muvaffaqiyatli amalga oshirildi! Balansingizga 1000 Cyber Coin qo'shildi.")

# ---------------------------------------------------------
# 5. ADMIN PANEL (STATISTIKA VA DAROMAD CONTROL)
# ---------------------------------------------------------
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Bu yerga o'z Telegram ID ingizni kiritishingiz mumkin
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT SUM(amount) FROM payments WHERE status='SUCCESS'") as c2:
            total_revenue = (await c2.fetchone())[0] or 0

    await message.answer(
        f"📊 **Admin Control Panel**\n\n"
        f"👤 Jami foydalanuvchilar: **{total_users} ta**\n"
        f"💰 Jami daromad: **{total_revenue} Telegram Stars**\n"
        f"🗄️ Baza holati: **SQL Active (SQLite)**",
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# 6. BOTNI ISHGA TUSHIRISH
# ---------------------------------------------------------
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
