import asyncio
import io
import logging
import os
import sqlite3
import sys

import qrcode
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    WebAppInfo,
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
router = Router()

# ==========================================
# 1. DATABASE (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int, full_name: str, username: str):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
        (user_id, full_name, username)
    )
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ==========================================
# 2. KEYBOARD & BUTTONS
# ==========================================
def main_keyboard():
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://telegram.org")
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Mini App-ni ochish",
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            ],
            [
                InlineKeyboardButton(text="📲 QR-kod yaratish", callback_data="qr_info"),
                InlineKeyboardButton(text="⭐ Telegram Stars To'lov", callback_data="pay_stars")
            ]
        ]
    )
    return keyboard

# ==========================================
# 3. HANDLERS
# ==========================================

# /start
@router.message(CommandStart())
async def start_handler(message: Message):
    add_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "yo'q"
    )
    
    await message.answer(
        f"Xush kelibsiz, <b>{message.from_user.full_name}</b>!\n\n"
        f"Pastdagi tugmalar orqali Mini App-ni ochishingiz yoki funksiyalardan foydalanishingiz mumkin.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

# /admin
@router.message(Command("admin"))
async def admin_handler(message: Message):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Bu buyruq faqat administrator uchun!")
        return

    users_count = get_total_users()
    await message.answer(
        f"📊 <b>Admin Panel:</b>\n\n"
        f"👥 Foydalanuvchilar soni: <b>{users_count}</b> ta",
        parse_mode="HTML"
    )

# /qr
@router.message(Command("qr"))
async def qr_generator_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Matn kiritilmadi! Misol: <code>/qr https://t.me/botingiz</code>", parse_mode="HTML")
        return

    text_to_encode = args[1]
    qr_img = qrcode.make(text_to_encode)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    photo = BufferedInputFile(buffer.getvalue(), filename="qrcode.png")
    await message.answer_photo(
        photo=photo,
        caption=f"✅ <b>QR-kod tayyor!</b>\n<code>{text_to_encode}</code>",
        parse_mode="HTML"
    )

# Mini App (Web App) dan qaytgan ma'lumotlarni qabul qilish
@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    data = message.web_app_data.data
    await message.answer(f"📩 Mini App-dan ma'lumot qabul qilindi: <code>{data}</code>", parse_mode="HTML")

# Callback handler (Tugmalar bosilganda)
@router.callback_query(F.data == "qr_info")
async def qr_info_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer("QR-kod yaratish uchun <code>/qr [matn]</code> formatida yuboring.", parse_mode="HTML")

# TELEGRAM STARS TO'LOV FUNKSIYASI
@router.callback_query(F.data == "pay_stars")
async def pay_stars_callback(call: CallbackQuery):
    await call.answer()
    prices = [LabeledPrice(label="VIP Obuna", amount=1)]  # 1 Telegram Star
    
    await call.message.answer_invoice(
        title="VIP Obuna Xaridi",
        description="1 oy muddatga botdan to'liq foydalanish imkoniyati",
        prices=prices,
        provider_token="",  # Telegram Stars uchun bo'sh qoldiriladi
        payload="vip_subscription_payload",
        currency="XTR"  # Telegram Stars valyutasi
    )

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    await message.answer("🎉 To'lov muvaffaqiyatli amalga oshirildi! VIP statusingiz faollashtirildi.")

# ==========================================
# 4. START BOT
# ==========================================

async def main():
    init_db()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logging.critical("BOT_TOKEN topilmadi!")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
