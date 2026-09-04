import os
import sqlite3
import logging
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, PreCheckoutQuery, ContentType, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ⚠️ SHU YERGA O'ZINGIZNING TELEGRAM ID RAQAMINGIZNI YOZING:
ADMIN_ID = 8898979946 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ==================== DATABASE ====================
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
            is_vip INTEGER DEFAULT 0
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
        return {"user_id": row[0], "full_name": row[1], "username": row[2], "balance": row[3], "coins": row[4], "is_vip": bool(row[5])}
    return None

def register_or_update_user(user_id: int, full_name: str, username: str):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, full_name, username, balance, coins, is_vip) VALUES (?, ?, ?, 0.0, 0, 0)", (user_id, full_name, username))
    else:
        cursor.execute("UPDATE users SET full_name = ?, username = ? WHERE user_id = ?", (full_name, username, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
    vip_users = cursor.fetchone()[0]
    conn.close()
    return total_users, vip_users

# ==================== KEYBOARDS ====================
def get_main_keyboard(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="🤖 Sun'iy Intellekt (AI)"), KeyboardButton(text="🎨 AI Rasm Yaratish")],
        [KeyboardButton(text="📥 Video Yuklagich"), KeyboardButton(text="📈 Kripto & Oltin")],
        [KeyboardButton(text="🔗 Link Qisqartirish"), KeyboardButton(text="🔤 Matn Tarjimon")],
        [KeyboardButton(text="📲 QR-Kod Yaratish"), KeyboardButton(text="🧮 Aqlli Kalkulyator")],
        [KeyboardButton(text="🌤 Aniq Ob-havo"), KeyboardButton(text="💎 Valyuta kurslari")],
        [KeyboardButton(text="📝 Shaxsiy Eslatmalar")]
    ]
    # Faqat admin uchun maxsus tugma:
    if is_admin:
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ==================== BOT HANDLERS ====================
@router.message(CommandStart())
async def cmd_start(message: Message):
    register_or_update_user(message.from_user.id, message.from_user.full_name, message.from_user.username or "")
    user_data = get_user_data(message.from_user.id)
    vip_status = "⭐ VIP A'zo" if user_data["is_vip"] else "Oddiy foydalanuvchi"
    
    is_admin = (message.from_user.id == ADMIN_ID)
    
    await message.answer(
        f"Xush kelibsiz, {user_data['full_name']}!\n\n"
        f"📌 Status: {vip_status}\n"
        f"💰 Balans: {user_data['balance']} UZS\n"
        f"🪙 Tangalar: {user_data['coins']} coin\n\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )

# 🔒 FAQAT ADMIN UCHUN ADMIN PANEL
@router.message(F.text == "⚙️ Admin Panel")
@router.message(Command("admin"))
async def admin_panel_handler(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ Kechirasiz, bu bo'lim faqat bot administratori uchun!")
        return

    total_users, vip_users = get_stats()
    
    await msg.answer(
        f"⚙️ **ADMIN PANEL**\n\n"
        f"👥 Jami foydalanuvchilar: **{total_users} ta**\n"
        f"⭐ VIP a'zolar: **{vip_users} ta**\n"
        f"💻 Tizim holati: **Ishchi holatda (Active)**"
    )

# Oddiy xizmatlar
@router.message(F.text == "🤖 Sun'iy Intellekt (AI)")
async def ai_handler(msg: Message):
    await msg.answer("🤖 **AI Chat:** Savolingizni yozib yuboring!")

@router.message(F.text == "🎨 AI Rasm Yaratish")
async def ai_image_handler(msg: Message):
    await msg.answer("🎨 Tasvirlamoqchi bo'lgan rasmingiz haqida matn yuboring:")

@router.message(F.text == "📥 Video Yuklagich")
async def video_downloader(msg: Message):
    await msg.answer("📥 Video havolasini yuboring:")

@router.message(F.text == "📈 Kripto & Oltin")
async def crypto_handler(msg: Message):
    await msg.answer("📈 **Bozor narxlari:**\n\n• BTC: $88,400\n• ETH: $3,250\n• Oltin (1g): 920,000 UZS")

@router.message(F.text == "🔗 Link Qisqartirish")
async def short_link_handler(msg: Message):
    await msg.answer("🔗 Qisqartirmoqchi bo'lgan havolangizni yuboring:")

@router.message(F.text == "🔤 Matn Tarjimon")
async def translator_handler(msg: Message):
    await msg.answer("🔤 Tarjima qilish uchun matn yuboring:")

@router.message(F.text == "📲 QR-Kod Yaratish")
async def qr_handler(msg: Message):
    await msg.answer("📲 QR-kod uchun matn yuboring:")

@router.message(F.text == "🧮 Aqlli Kalkulyator")
async def calc_handler(msg: Message):
    await msg.answer("🧮 Matematik ifodani kiriting:")

@router.message(F.text == "🌤 Aniq Ob-havo")
async def weather_handler(msg: Message):
    await msg.answer("🌤 Shahar nomini yuboring:")

@router.message(F.text == "💎 Valyuta kurslari")
async def currency_handler(msg: Message):
    await msg.answer("💎 **Kurslar:**\n\n• 1 USD = 12,850 UZS\n• 1 EUR = 13,900 UZS")

@router.message(F.text == "📝 Shaxsiy Eslatmalar")
async def notes_handler(msg: Message):
    await msg.answer("📝 Eslatmalaringiz bo'sh.")

# ==================== RENDER DUMMY SERVER ====================
async def handle(request):
    try:
        with open("miniapp.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type='text/html')
    except:
        return web.Response(text="Bot Web Service Active")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ==================== ENTRYPOINT ====================
async def main():
    init_db()
    asyncio.create_task(start_dummy_server())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
