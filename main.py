import os
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Render domeningiz aniq ko'rsatilgan
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://telegram-bot-7n6t.onrender.com")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_PATH = "database.db"

# --- DATABASE INIT ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                is_vip INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
        await db.commit()

async def set_vip(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

# --- BOT HANDLERS ---

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await add_user(message.from_user.id, message.from_user.full_name)
    
    # Telegram Bot ichidagi tugma (Mini App)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ VIP Status & SaaS App",
                    web_app=WebAppInfo(url=f"{RENDER_URL}/miniapp")
                )
            ]
        ]
    )
    await message.answer(
        f"👋 Salom, **{message.from_user.first_name}**!\n\n"
        "**Mega AI & SaaS Assistant** platformasiga xush kelibsiz.\n"
        "Quyidagi tugma orqali Mini App interfeysiga kiring:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(F.text == "/admin")
async def admin_cmd(message: types.Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1") as cursor:
            vip_users = (await cursor.fetchone())[0]

    await message.answer(
        f"📊 **Admin Boshqaruv Paneli**\n\n"
        f"👥 Jami foydalanuvchilar: **{total_users}** ta\n"
        f"👑 VIP a'zolar: **{vip_users}** ta\n"
        f"💰 Umumiy tushum: **{vip_users * 100} ⭐️**",
        parse_mode="Markdown"
    )

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await set_vip(message.from_user.id)
    await message.answer("🎉 **Tabriklaymiz!** Siz muvaffaqiyatli VIP statusga ega bo'ldingiz.")

# --- WEB ROUTES ---

async def serve_miniapp(request):
    return web.FileResponse('./templates/miniapp.html')

async def create_stars_invoice(request):
    try:
        data = await request.json()
        user_id = data.get("user_id")

        if not user_id:
            return web.json_response({"ok": False, "error": "User ID topilmadi"}, status=400)

        invoice_link = await bot.create_invoice_link(
            title="VIP Status Obunasi",
            description="1 Oylik Premium VIP kirish huquqi",
            payload=f"vip_sub_{user_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="VIP Access", amount=100)]
        )
        return web.json_response({"ok": True, "invoice_url": invoice_link})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def health_check(request):
    return web.Response(text="Bot is Live!")

# --- MAIN RUNNER ---

async def main():
    await init_db()
    
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/miniapp', serve_miniapp)
    app.router.add_post('/api/create-invoice', create_stars_invoice)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
