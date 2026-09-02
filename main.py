import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo, 
    LabeledPrice, 
    PreCheckoutQuery
)

# --- SOZLAMALAR ---
ADMIN_ID = 8898979946  # O'zingizning Telegram ID-ingiz
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "TEST:PROVIDER_TOKEN")
MINI_APP_URL = "https://telegram-bot-7n6t.onrender.com"  # HTML fayl manzili
SPONSOR_CHANNELS = ["@demo_kanal1"]  # Homiy kanallari

router = Router()

# --- KLAVIATURALAR ---
def get_main_keyboard(user_id: int):
    buttons = [
        [InlineKeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=MINI_APP_URL))],
        [
            InlineKeyboardButton(text="🤖 Sun'iy Intellekt (AI)", callback_data="ai_chat"),
            InlineKeyboardButton(text="🎨 AI Rasm Yaratish", callback_data="ai_image")
        ],
        [
            InlineKeyboardButton(text="📥 Video Yuklagich", callback_data="video_downloader"),
            InlineKeyboardButton(text="📈 Kripto & Oltin", callback_data="crypto_gold")
        ],
        [
            InlineKeyboardButton(text="🔗 Link Qisqartirish", callback_data="link_shortener"),
            InlineKeyboardButton(text="🔤 Matn Tarjimon", callback_data="translator")
        ],
        [
            InlineKeyboardButton(text="📲 QR-Kod Yaratish", callback_data="qr_code"),
            InlineKeyboardButton(text="🧮 Aqlli Kalkulyator", callback_data="calculator")
        ],
        [
            InlineKeyboardButton(text="🌤 Aniq Ob-havo", callback_data="weather"),
            InlineKeyboardButton(text="💎 Valyuta kurslari", callback_data="currency")
        ],
        [
            InlineKeyboardButton(text="📝 Shaxsiy Eslatmalar", callback_data="notes"),
            InlineKeyboardButton(text="⭐ VIP Obuna Olish", callback_data="buy_vip")
        ],
        [InlineKeyboardButton(text="🚀 Loyihani Sotib Olish (7 Mln UZS)", callback_data="buy_bot_project")]
    ]
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERLAR ---
@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 **Mega AI Assistant botiga xush kelibsiz!**\n\nQuyidagi menyudan kerakli xizmatni tanlang:", 
        reply_markup=get_main_keyboard(user_id=message.from_user.id),
        parse_mode="Markdown"
    )

# 7 Mln loyiha taqdimoti
@router.callback_query(F.data == "buy_bot_project")
async def sell_bot_handler(call: types.CallbackQuery):
    text = (
        "🚀 **Mega AI Assistant — Tayyor Biznes Loyiha!**\n\n"
        "• 🎮 **Mini App O'yinlar Hubi** (HTML5 o'yinlar)\n"
        "• 🤖 **AI Chat & AI Rasm Yaratish**\n"
        "• 💳 **Click / Payme Avto-to'lov tizimi**\n"
        "• 📢 **Majburiy Obuna (Kanal o'stirish engine)**\n"
        "• ⚡ **24/7 Uptime Render serveri**\n\n"
        "💰 **Loyiha Narxi:** 7 000 000 UZS"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Admin bilan bog'lanish", url="https://t.me/admin_username")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# VIP to'lov yuborish
@router.callback_query(F.data == "buy_vip")
async def buy_vip_handler(call: types.CallbackQuery, bot: Bot):
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="⭐ VIP Obuna (1 Oylik)",
        description="Cheksiz AI va Mini App imkoniyatlari!",
        payload="vip_subscription",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label="VIP Obuna", amount=5000000)] # 50,000 UZS
    )

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Admin Panel (Faqat ADMIN_ID uchun)
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    text = "⚙️ **Admin Panel**\n\n📊 Jami a'zolar: 12,450 ta\n💰 Oylik tushum: 3,500,000 UZS"
    await call.message.answer(text, parse_mode="Markdown")

# --- RENDER 24/7 SERVER & MAIN ---
async def handle_ping(request):
    return web.Response(text="Bot 24/7 active!")

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
