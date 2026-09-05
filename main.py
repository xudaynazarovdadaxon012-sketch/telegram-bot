import os
import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Render'dagi Environment Variable'dan tokenni olish
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. Ma'lumotlar bazasini yaratish va sozlash
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, username, coins) VALUES (?, ?, ?)", (user_id, username, 0.0))
        conn.commit()
        coins = 0.0
    else:
        coins = row[0]
    conn.close()
    return coins

# 2. /start buyrug'i va Web App tugmasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    coins = get_or_create_user(user_id, username)

    # Mini App-ni ochish uchun tugma
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎮 Prime CS Online-ni Ochish",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="🪙 Balansni Tekshirish", callback_data="check_balance")
        ]
    ])

    await message.answer(
        f"Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
        f"🎮 <b>Prime CS Online</b> 3D multiplayer o'yiniga tayyormisiz?\n"
        f"💰 Balansingiz: <b>{coins:.1f} Coin</b>\n\n"
        f"O'yinni boshlash uchun pastdagi tugmani bosing:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# 3. Balansni tekshirish tugmasi
@dp.callback_query(F.data == "check_balance")
async def process_balance_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    coins = get_or_create_user(user_id, callback.from_user.username or "")
    await callback.answer(f"Sizning balansingiz: {coins:.1f} Coin", show_alert=True)

# Main ishga tushirish funksiyasi
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("🤖 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
