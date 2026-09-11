import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from database import init_db, get_or_create_user, claim_daily_streak, set_vip

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://xudaynazarovdadaxon012-sketch.github.io/telegram-bot/")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render uchun dummy HTTP handler
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def check_subscription(user_id: int) -> bool:
    if not SPONSOR_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    user = get_or_create_user(user_id, referrer_id)
    
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        channel_clean = SPONSOR_CHANNEL.replace('@', '')
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{channel_clean}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ])
        await message.answer("⚠️ Botdan foydalanish uchun majburiy homiy kanalga a'zo bo'ling:", reply_markup=kb)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Ultra Cyber Hub (10 Modul)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🎁 Kunlik Bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="⭐ VIP Status (Telegram Stars)", callback_data="buy_stars")]
    ])
    
    await message.answer(
        f"👋 Salom, **{message.from_user.first_name}**!\n\n"
        f"💰 Balansingiz: **{user[1]} Coins**\n"
        f"👥 Taklif qilgan do'stlaringiz: **{user[2]} ta**\n\n"
        f"Pastdagi tugma orqali Mini App-ni oching:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await start_handler(callback.message)
    else:
        await callback.answer("❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True)

@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_handler(callback: types.CallbackQuery):
    status, streak, reward = claim_daily_streak(callback.from_user.id)
    if status:
        await callback.answer(f"🎉 Tabriklaymiz! {streak}-kunlik bonus: +{reward} Coins!", show_alert=True)
    else:
        await callback.answer("⚠️ Siz bugungi bonusni olib bo'lgansiz. Ertaga qayta kiring!", show_alert=True)

@dp.callback_query(F.data == "buy_stars")
async def send_invoice(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="VIP Maqom", amount=50)]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Maqom xaridi",
        description="Botda reklamasiz rejim va eksklyuziv imkoniyatlarni yoqish.",
        payload="vip_status_pack",
        currency="XTR",
        prices=prices
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    set_vip(message.from_user.id)
    await message.answer("🎉 To'lov muvaffaqiyatli amalga oshirildi! VIP maqomingiz faollashtirildi.")

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Render port xatosini bartaraf etish
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Bot Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
