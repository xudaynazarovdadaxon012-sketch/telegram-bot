import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://telegram-bot-7n6t.onrender.com")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- BOT HANDLERS ---

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ VIP Status (Mini App)",
                    web_app=WebAppInfo(url=f"{RENDER_URL}/miniapp")
                )
            ],
            [
                InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help_info")
            ]
        ]
    )
    await message.answer(
        f"👋 Salom, **{message.from_user.first_name}**!\n\n"
        "**Mega AI Assistant** SaaS loyihasiga xush kelibsiz.\n"
        "VIP imkoniyatlarni faollashtirish uchun pastdagi tugmani bosing:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "help_info")
async def help_callback(call: types.CallbackQuery):
    await call.message.answer("💡 Ushbu bot va Mini App orqali VIP obunalarni Telegram Stars valyutasida xarid qilishingiz mumkin.")
    await call.answer()

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await message.answer("🎉 **Tabriklaymiz!** To'lovingiz muvaffaqiyatli qabul qilindi. VIP status faollashtirildi!")

# --- WEB SERVER ROUTES ---

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
