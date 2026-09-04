import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

# Render yoki .env faylidan o'zgaruvchilarni olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://telegram-bot-7n6t.onrender.com")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8898979946"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render Environment Variables qismini tekshiring.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Dinamik menyu yaratuvchi funksiya
def get_main_menu(user_id: int):
    keyboard_layout = [
        [
            KeyboardButton(
                text="🎮 Mini App (O'yinlar Hub)",
                web_app=WebAppInfo(url=MINI_APP_URL),
            ),
        ],
        [
            KeyboardButton(text="🤖 Sun'iy Intellekt (AI)"),
            KeyboardButton(text="🎨 AI Rasm Yaratish"),
        ],
        [
            KeyboardButton(text="📹 Video Yuklagich"),
            KeyboardButton(text="📈 Kripto & Oltin"),
        ],
        [
            KeyboardButton(text="🔗 Link Qisqartirish"),
            KeyboardButton(text="🔤 Matn Tarjimon"),
        ],
        [
            KeyboardButton(text="📱 QR-Kod Yaratish"),
            KeyboardButton(text="🧮 Aqlli Kalkulyator"),
        ],
        [
            KeyboardButton(text="🌤 Aniq Ob-havo"),
            KeyboardButton(text="💎 Valyuta kurslari"),
        ],
        [
            KeyboardButton(text="📝 Shaxsiya Eslatmalar"),
            KeyboardButton(text="⭐ VIP Obuna"),
        ],
    ]

    # Faqat ADMIN_ID ga mos foydalanuvchiga Admin Panel tugmasi ko'rinadi
    if user_id == ADMIN_ID:
        keyboard_layout.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)


# ==================== HANDLERLAR ====================


# Start buyrug'i
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_menu = get_main_menu(message.from_user.id)
    await message.answer(
        "👋 Xush kelibsiz! Kerakli bo'limni pastdagi menyudan tanlang:",
        reply_markup=user_menu,
    )


# ⚙️ Admin Panel (Faqat ADMIN_ID uchun)
@dp.message_handler(lambda msg: msg.text == "⚙️ Admin Panel")
async def admin_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        channels_str = "\n".join(SPONSOR_CHANNELS)
        await message.answer(
            f"⚙️ **Admin Panel**\n\n"
            f"👤 **Admin ID:** `{ADMIN_ID}`\n"
            f"🌐 **Mini App:** {MINI_APP_URL}\n"
            f"📢 **Sponsor kanallar:**\n{channels_str}",
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ Sizda admin panelga kirish huquqi yo'q!")


# ⭐ VIP Obuna (To'lov tizimi integratsiyasi)
@dp.message_handler(lambda msg: msg.text == "⭐ VIP Obuna")
async def vip_handler(message: types.Message):
    PRICES = [
        LabeledPrice(label="VIP Obuna (1 oy)", amount=1500000)
    ]  # 15000.00 UZS
    await bot.send_invoice(
        message.chat.id,
        title="⭐ VIP Obuna",
        description="Botning barcha eksklyuziv imkoniyatlaridan cheklovsiz foydalanish.",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=PRICES,
        start_parameter="vip-subscription",
        payload="vip_access_payload",
    )


# Pre-checkout check (To'lovni tasdiqlash)
@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(
    pre_checkout_query: types.PreCheckoutQuery,
):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# Muvaffaqiyatli to'lov qayta ishlash
@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    await message.answer(
        "🎉 Muvaffaqiyatli to'lov amalga oshirildi! VIP maqomi faollashtirildi."
    )


# 🤖 Sun'iy Intellekt (AI)
@dp.message_handler(lambda msg: msg.text == "🤖 Sun'iy Intellekt (AI)")
async def ai_handler(message: types.Message):
    await message.answer(
        "🤖 **AI Yordamchi:**\nSizni qiziqtirgan har qanday savolni yozib yuboring:"
    )


# 🎨 AI Rasm Yaratish
@dp.message_handler(lambda msg: msg.text == "🎨 AI Rasm Yaratish")
async def ai_image_handler(message: types.Message):
    await message.answer(
        "🎨 **AI Rasm Generator:**\nYaratmoqchi bo'lgan rasmingiz haqida batafsil matn (prompt) yuboring:"
    )


# 📹 Video Yuklagich
@dp.message_handler(lambda msg: msg.text == "📹 Video Yuklagich")
async def video_downloader_handler(message: types.Message):
    await message.answer(
        "📹 **Video Yuklagich:**\nInstagram, YouTube yoki TikTok video havolasini (link) yuboring:"
    )


# 📈 Kripto & Oltin
@dp.message_handler(lambda msg: msg.text == "📈 Kripto & Oltin")
async def crypto_handler(message: types.Message):
    await message.answer(
        "📈 **Kripto va Oltin Narxlari:**\n\n"
        "🟡 **Oltin (1g):** 910,000 UZS\n"
        "🪙 **Bitcoin (BTC):** $64,200\n"
        "💎 **Ethereum (ETH):** $3,450\n"
        "⚡ **TON:** $6.80",
        parse_mode="Markdown",
    )


# 🔗 Link Qisqartirish
@dp.message_handler(lambda msg: msg.text == "🔗 Link Qisqartirish")
async def url_shortener_handler(message: types.Message):
    await message.answer(
        "🔗 **Link Qisqartirish:**\nQisqartirmoqchi bo'lgan uzun havolangizni yuboring:"
    )


# 🔤 Matn Tarjimon
@dp.message_handler(lambda msg: msg.text == "🔤 Matn Tarjimon")
async def translator_handler(message: types.Message):
    await message.answer(
        "🔤 **Matn Tarjimon:**\nTarjima qilmoqchi bo'lgan matningizni yuboring (O'zbek/Ingliz/Rus):"
    )


# 📱 QR-Kod Yaratish
@dp.message_handler(lambda msg: msg.text == "📱 QR-Kod Yaratish")
async def qr_code_handler(message: types.Message):
    await message.answer(
        "📱 **QR-Kod Yaratish:**\nQR-kodga aylantirmoqchi bo'lgan matn yoki havolani yuboring:"
    )


# 🧮 Aqlli Kalkulyator
@dp.message_handler(lambda msg: msg.text == "🧮 Aqlli Kalkulyator")
async def calculator_handler(message: types.Message):
    await message.answer(
        "🧮 **Aqlli Kalkulyator:**\nMatematik ifodani yozing (masalan: `25 * 4 + 100`):",
        parse_mode="Markdown",
    )


# 🌤 Aniq Ob-havo
@dp.message_handler(lambda msg: msg.text == "🌤 Aniq Ob-havo")
async def weather_handler(message: types.Message):
    await message.answer(
        "🌤 **Aniq Ob-havo:**\nOb-havosini bilmoqchi bo'lgan shahar nomini kiriting (masalan: Toshkent, Samarqand):"
    )


# 💎 Valyuta kurslari
@dp.message_handler(lambda msg: msg.text == "💎 Valyuta kurslari")
async def currency_handler(message: types.Message):
    await message.answer(
        "💎 **Markaziy Bank Valyuta Kurslari:**\n\n"
        "🇺🇸 **USD:** 12,680 UZS\n"
        "🇪🇺 **EUR:** 13,850 UZS\n"
        "🇷🇺 **RUB:** 142 UZS",
        parse_mode="Markdown",
    )


# 📝 Shaxsiya Eslatmalar
@dp.message_handler(lambda msg: msg.text == "📝 Shaxsiya Eslatmalar")
async def notes_handler(message: types.Message):
    await message.answer(
        "📝 **Shaxsiy Eslatmalar:**\nSaqlab qo'ymoqchi bo'lgan eslatmangizni yuboring:"
    )


# Noma'lum buyruq va matnlar uchun fallback
@dp.message_handler()
async def unknown_command(message: types.Message):
    user_menu = get_main_menu(message.from_user.id)
    await message.answer(
        "⚠️ Noma'lum buyruq. Iltimos, pastdagi menyudan foydalaning:",
        reply_markup=user_menu,
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
