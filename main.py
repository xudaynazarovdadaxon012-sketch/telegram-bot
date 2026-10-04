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
    LabeledPrice,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
)
from aiohttp import web

# O'zgaruvchilarni yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@kanalingiz_usernamesi")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# VIP foydalanuvchilarni saqlash uchun (Vaqtincha xotira, bazasiz test uchun)
VIP_USERS = set()


# Render xizmati uchun soxta veb-server
async def handle(request):
    return web.FileResponse("index.html")


# Majburiy obunani tekshirish
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID, user_id=user_id
        )
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True


# Inline tugmalar
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
                    text="⭐ VIP Obuna / Stars", callback_data="vip_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Qo'llab-quvvatlash / Admin",
                    url="https://t.me/admin_usernameringiz",
                )
            ],
        ]
    )


# Asosiy menyu (Reply Keyboard)
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎮 Barcha o'yinlar"),
                KeyboardButton(text="🔥 Top o'yinlar"),
            ],
            [
                KeyboardButton(text="🎁 Kunlik bepul demo"),
                KeyboardButton(text="💎 VIP Imkoniyatlar"),
            ],
            [
                KeyboardButton(text="ℹ️ Yordam va Qo'llanma"),
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
            "Botdan foydalanish uchun rasmiy kanalimizga obuna bo'ling:",
            parse_mode="HTML",
            reply_markup=get_inline_keyboard(is_subbed=False),
        )
        return

    caption_text = (
        f"🎮 Assalomu alaykum <b>{user_name}</b>, <b>Game Hub</b> botiga xush kelibsiz!\n\n"
        "Siz bu yerda eng mashhur o'yinlarni qulay tarzda yuklab olishingiz mumkin.\n\n"
        "👇 Kerakli bo'limni pastki menyudan tanlang:"
    )

    await message.answer_photo(
        photo="https://picsum.photos/800/400",
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
            "✅ Rahmat! Obuna tasdiqlandi. Qaytadan /start bosing."
        )
    else:
        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True
        )


# Bepul o'yinlar bo'limi
@dp.message(F.text == "🎮 Barcha o'yinlar")
async def free_games_handler(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏎️ SuperTuxKart (3D Poyga)",
                    callback_data="dl_supertux",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏗️ Mindustry (Strategiya)",
                    callback_data="dl_mindustry",
                )
            ],
        ]
    )
    await message.answer(
        "🎮 <b>Bepul O'yinlar Katalogi:</b>\n\nYuklab olish uchun o'yinni tanlang:",
        parse_mode="HTML",
        reply_markup=kb,
    )


# Bepul o'yin havolalarini yuborish
@dp.callback_query(F.data.startswith("dl_"))
async def download_game(callback: types.CallbackQuery):
    game = callback.data.split("_")[1]
    if game == "supertux":
        url = "https://supertuxkart.net/Downloads"
        name = "SuperTuxKart"
    else:
        url = "https://mindustrygame.github.io/"
        name = "Mindustry"

    await callback.message.answer(
        f"📥 <b>{name}</b> o'yinini yuklab olish havolasi:\n{url}",
        parse_mode="HTML",
    )
    await callback.answer()


# VIP Bo'lim
@dp.message(F.text == "💎 VIP Imkoniyatlar")
@dp.callback_query(F.data == "vip_menu")
async def vip_games_handler(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    message = event if isinstance(event, types.Message) else event.message

    if user_id in VIP_USERS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚗 GTA Liberty City Stories (PSP)",
                        callback_data="dl_gta_lcs",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏙️ GTA Vice City Stories (PSP)",
                        callback_data="dl_gta_vcs",
                    )
                ],
            ]
        )
        await message.answer(
            "💎 <b>Siz VIP a'zosiz!</b>\n\nEksklyuziv o'yinlarni yuklab oling:",
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⭐ VIP Obuna Olish (50 Stars)",
                        callback_data="buy_vip_50",
                    )
                ]
            ]
        )
        await message.answer(
            "💎 <b>VIP Bo'lim (Eksklyuziv O'yinlar)</b>\n\n"
            "Ushbu bo'limda quyidagi o'yinlar mavjud:\n"
            "• <b>GTA: Liberty City Stories (PSP)</b>\n"
            "• <b>GTA: Vice City Stories (PSP)</b>\n\n"
            "VIP obunani Telegram Stars orqali xarid qiling:",
            parse_mode="HTML",
            reply_markup=kb,
        )

    if isinstance(event, types.CallbackQuery):
        await event.answer()


# Telegram Stars to'lovini shakllantirish
@dp.callback_query(F.data == "buy_vip_50")
async def send_invoice(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Obuna",
        description="Eksklyuziv GTA (PSP) o'yinlarini yuklab olish huquqi.",
        payload="vip_sub_50_stars",
        currency="XTR",  # Telegram Stars kodi
        prices=[LabeledPrice(label="VIP Obuna", amount=50)],
    )
    await callback.answer()


# To'lovni tasdiqlash
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# To'lov muvaffaqiyatli amalga oshganda
@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    user_id = message.from_user.id
    VIP_USERS.add(user_id)  # Foydalanuvchini VIP ro'yxatga qo'shish

    await message.answer(
        "🎉 <b>Tabriklaymiz!</b> VIP obuna muvaffaqiyatli faollashtirildi.\n\n"
        "Endi <b>💎 VIP Imkoniyatlar</b> tugmasini bosib, eksklyuziv o'yinlarni yuklab olishingiz mumkin!",
        parse_mode="HTML",
    )


async def main():
    logging.basicConfig(level=logging.INFO)

    # Render uchun aiohttp veb-serveri
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
