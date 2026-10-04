import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiohttp import web

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv(
    "CHANNEL_ID", "@kanalingiz_usernamesi"
)  # Majburiy obuna kanali
MINI_APP_URL = os.getenv(
    "MINI_APP_URL", "https://render-app-nomingiz.onrender.com"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Render'da "Web Service" port-binding xatosi bermasligi uchun soxta veb-server
async def handle(request):
    return web.Response(text="Game Hub Bot ishlamoqda!")


# Majburiy obunani tekshirish funksiyasi
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID, user_id=user_id
        )
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True  # Kanal sozlanmagan bo'lsa, o'tkazib yuboradi


# Post ostidagi tugmalar (Mini App va VIP)
def get_inline_keyboard(is_subbed=True):
    if not is_subbed:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 Kanalga a'zo bo'lish",
                        url=f"https://t.me/{CHANNEL_ID.replace('@', '')}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Tekshirish", callback_data="check_sub"
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Play Hub (Mini App)",
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ VIP Obuna / Stars", callback_data="vip_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Aloqa / Admin",
                    url="https://t.me/admin_usernameringiz",
                )
            ],
        ]
    )


# O'yinlar botiga mos keladigan asosiy menyu (Reply Keyboard)
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🕹️ Play Hub-ni ochish",
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ],
            [
                KeyboardButton(text="🔥 Mashhur o'yinlar"),
                KeyboardButton(text="💎 VIP Imkoniyatlar"),
            ],
            [
                KeyboardButton(text="🎁 Kunlik demo"),
                KeyboardButton(text="ℹ️ Yordam"),
            ],
        ],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    is_subbed = await check_subscription(user_id)

    if not is_subbed:
        await message.answer(
            f"Assalomu alaykum <b>{user_name}</b>!\n\n"
            "Botdan foydalanish va o'yinlarni yuklash uchun rasmiy kanalimizga obuna bo'ling:",
            parse_mode="HTML",
            reply_markup=get_inline_keyboard(is_subbed=False),
        )
        return

    caption_text = (
        f"🎮 Assalomu alaykum <b>{user_name}</b>, **Game Hub** botiga xush kelibsiz!\n\n"
        "Siz bu yerda eng so'nggi va ommabop o'yinlarni yuklab olishingiz "
        "hamda Mini App do'konimizdan foydalanishingiz mumkin.\n\n"
        "👇 Kerakli bo'limni tanlang:"
    )

    await message.answer_photo(
        photo="https://picsum.photos/800/400",  # O'zingizning banner rasmingiz
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=get_inline_keyboard(is_subbed=True),
    )
    await message.answer(
        "Bo'limni tanlang 👇", reply_markup=get_main_menu()
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    is_subbed = await check_subscription(callback.from_user.id)
    if is_subbed:
        await callback.message.delete()
        await callback.message.answer(
            "✅ Rahmat! Obuna tasdiqlandi. Endi /start bosing."
        )
    else:
        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True
        )


async def main():
    logging.basicConfig(level=logging.INFO)

    # Render Web Service uchun port eshituvchisini ulash
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    asyncio.create_task(site.start())

    # Botni ishga tushirish
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
