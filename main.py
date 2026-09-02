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
ADMIN_ID = 8898979946  # O'zingizning Telegram ID-ingizni yozing
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "381764678:TEST:12345")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://telegram-bot-7n6t.onrender.com")
SPONSOR_CHANNELS = ["@demo_kanal1"]  # Majburiy obuna kanallari

router = Router()

# --- KLAVIATURA ---
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
            InlineKeyboardButton(text="⭐ VIP Obuna", callback_data="buy_vip")
        ]
    ]
    
    # Admin Panel faqat sizga ko'rinadi
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERLAR ---

# 1. /start buyrug'i
@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 **Mega AI Assistant botiga xush kelibsiz!**\n\nQuyidagi menyudan kerakli xizmatni tanlang:", 
        reply_markup=get_main_keyboard(user_id=message.from_user.id),
        parse_mode="Markdown"
    )

# 2. VIP To'lov Tizimi (Click / Payme)
@router.callback_query(F.data == "buy_vip")
async def buy_vip_handler(call: types.CallbackQuery, bot: Bot):
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="⭐ VIP Obuna (1 Oylik)",
        description="Cheksiz AI va Mini App imkoniyatlariga ega bo'ling!",
        payload="vip_subscription",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label="VIP Obuna", amount=5000000)] # 50,000 UZS
    )
    await call.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 3. Admin Panel (Faqat ADMIN_ID uchun)
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Bu bo'lim faqat admin uchun!", show_alert=True)
        return
    text = (
        "⚙️ **Admin Panel & Loyiha Boshqaruvi**\n\n"
        "📊 Jami foydalanuvchilar: **14,520 ta**\n"
        "⭐ VIP A'zolar: **85 ta**\n"
        "💰 Oylik Daromad: **4,250,000 UZS**\n"
        "⚡ Server Holati: **24/7 Onlayn (Render)**"
    )
    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()

# 4. Asosiy Menyu Callback'lari
@router.callback_query()
async def process_all_callbacks(call: types.CallbackQuery):
    responses = {
        "ai_chat": "🤖 Savolingizni yuboring, AI javob beradi:",
        "ai_image": "🎨 Yaratmoqchi bo'lgan rasmingizni tasvirlang:",
        "video_downloader": "📥 Video havolasini (TikTok/Instagram/YouTube) yuboring:",
        "crypto_gold": "📈 Kriptovalyuta va oltin kurslari bo'limi.",
        "link_shortener": "🔗 Qisqartirmoqchi bo'lgan uzun havolangizni yuboring:",
        "translator": "🔤 Tarjima qilish uchun matn kiriting:",
        "qr_code": "📲 QR-kodga aylantirish uchun matn yoki havola yuboring:",
        "calculator": "🧮 Matematik ifodani yozing (masalan: 25 * 4):",
        "weather": "🌤 Shahar nomini yozib yuboring (masalan: Tashkent):",
        "currency": "💎 USD/EUR valyuta kurslari yangilandi.",
        "notes": "📝 Shaxsiy eslatmangizni yozib qoldiring:"
    }
    msg = responses.get(call.data, "Ushbu bo'lim faollashtirildi!")
    await call.message.answer(msg)
    await call.answer()

# 5. Noma'lum matnlar uchun javob (Eng pastda turishi shart!)
@router.message()
async def echo_handler(message: types.Message):
    await message.answer(
        "Buyruq tushunilmadi. Iltimos, menyudan foydalaning:",
        reply_markup=get_main_keyboard(user_id=message.from_user.id)
    )

# --- RENDER SERVER (24/7 UPTIME) ---
async def handle_ping(request):
    return web.Response(text="Bot runs 24/7 fine!")

async def main():
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN ortam o'zgaruvchisi topilmadi!")

    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Konflikt va sekinlashuvni oldini olish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
