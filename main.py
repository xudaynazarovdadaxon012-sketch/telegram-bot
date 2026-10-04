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

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@kanalingiz_usernamesi")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VIP_USERS = set()

# O'yinlar bazasi (10 ta o'yin)
GAMES_DATABASE = {
    # BEPUL O'YINLAR (6 ta)
    "nfs": {
        "title": "🏎 Need for Speed: Most Wanted (PSP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "minecraft": {
        "title": "⛏ Minecraft PE v1.20 (Android/APK)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "pes": {
        "title": "⚽ eFootball PES 2024 (PPSSPP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "subway": {
        "title": "🏃 Subway Surfers (Mod Money APK)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "tekken": {
        "title": "🥊 Tekken 6 (PPSSPP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "asphalt": {
        "title": "🚘 Asphalt 9: Legends (APK)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    # VIP O'YINLAR (4 ta)
    "gta_lcs": {
        "title": "🚗 GTA: Liberty City Stories (PSP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "gta_vcs": {
        "title": "🏙 GTA: Vice City Stories (PSP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "god_of_war": {
        "title": "⚔ God of War: Ghost of Sparta (PSP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "mortal_kombat": {
        "title": "🐉 Mortal Kombat Unchained (PSP/ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
}


async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID, user_id=user_id
        )
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎮 Barcha o'yinlar (10+)"),
                KeyboardButton(text="💎 VIP Imkoniyatlar"),
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="👨‍💻 Admin bilan aloqa"),
            ],
        ],
        resize_keyboard=True,
    )


def get_sub_keyboard():
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
                    text="✅ Obunani tekshirish", callback_data="check_sub"
                )
            ],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if not await check_subscription(user_id):
        await message.answer(
            f"Assalomu alaykum <b>{user_name}</b>!\n\n"
            "Botdan foydalanish uchun rasmiy kanalimizga obuna bo'ling:",
            parse_mode="HTML",
            reply_markup=get_sub_keyboard(),
        )
        return

    await message.answer(
        f"🔥 <b>Game Hub Store</b> botiga xush kelibsiz!\n\n"
        "Siz bu yerda TOP 10+ Android va PPSSPP (PSP) o'yinlarini bir zumda yuklab olishingiz mumkin.\n\n"
        "👇 Bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ Obuna tasdiqlandi! Menyudan foydalanishingiz mumkin.",
            reply_markup=get_main_menu(),
        )
    else:
        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True
        )


# Bepul o'yinlar ro'yxati (6 ta o'yin)
@dp.message(F.text == "🎮 Barcha o'yinlar (10+)")
async def free_games_handler(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏎 Need for Speed Most Wanted",
                    callback_data="game_nfs",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛏ Minecraft PE v1.20", callback_data="game_minecraft"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚽ eFootball PES 2024", callback_data="game_pes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏃 Subway Surfers (MOD)", callback_data="game_subway"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥊 Tekken 6 ISO", callback_data="game_tekken"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚘 Asphalt 9 Legends", callback_data="game_asphalt"
                )
            ],
        ]
    )
    await message.answer(
        "🎮 <b>BEPUL O'YINLAR KATALOGI:</b>\n\nYuklab olish uchun o'yinni tanlang:",
        parse_mode="HTML",
        reply_markup=kb,
    )


# VIP Bo'lim (4 ta o'yin)
@dp.message(F.text == "💎 VIP Imkoniyatlar")
async def vip_games_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id in VIP_USERS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚗 GTA Liberty City Stories",
                        callback_data="game_gta_lcs",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏙 GTA Vice City Stories",
                        callback_data="game_gta_vcs",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚔ God of War Ghost of Sparta",
                        callback_data="game_god_of_war",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🐉 Mortal Kombat Unchained",
                        callback_data="game_mortal_kombat",
                    )
                ],
            ]
        )
        await message.answer(
            "💎 <b>Siz VIP a'zosiz!</b>\n\nEksklyuziv TOP o'yinlarni yuklab oling:",
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
            "• 🚗 <b>GTA: Liberty City Stories</b>\n"
            "• 🏙 <b>GTA: Vice City Stories</b>\n"
            "• ⚔ <b>God of War: Ghost of Sparta</b>\n"
            "• 🐉 <b>Mortal Kombat Unchained</b>\n\n"
            "VIP obunani Telegram Stars orqali xarid qilib, barchasini oching:",
            parse_mode="HTML",
            reply_markup=kb,
        )


# Fayllarni lahzada yuborish
@dp.callback_query(F.data.startswith("game_"))
async def send_game_file(callback: types.CallbackQuery):
    game_key = callback.data.replace("game_", "")
    game_data = GAMES_DATABASE.get(game_key)

    if game_data:
        await callback.message.answer_document(
            document=game_data["file"],
            caption=f"✅ <b>{game_data['title']}</b> fayli tayyor!",
            parse_mode="HTML",
        )
    await callback.answer()


# Telegram Stars to'lovi
@dp.callback_query(F.data == "buy_vip_50")
async def send_invoice(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Obuna",
        description="Eksklyuziv GTA, God of War va Mortal Kombat o'yinlarini yuklab olish huquqi.",
        payload="vip_sub_50_stars",
        currency="XTR",
        prices=[LabeledPrice(label="VIP Obuna", amount=50)],
    )
    await callback.answer()


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    VIP_USERS.add(message.from_user.id)
    await message.answer(
        "🎉 <b>Tabriklaymiz!</b> VIP obunangiz faollashtirildi.\n\n"
        "Endi <b>💎 VIP Imkoniyatlar</b> bo'limidagi barcha eksklyuziv o'yinlarni yuklab olishingiz mumkin!",
        parse_mode="HTML",
    )


@dp.message(F.text == "📊 Statistika")
async def stats_handler(message: types.Message):
    await message.answer(
        "📊 <b>Bot Statistikasi:</b>\n\n"
        "• Baza o'yinlari: 10+ ta\n"
        "• Tizim holati: 🟢 Aktiv (24/7 Server)",
        parse_mode="HTML",
    )


@dp.message(F.text == "👨‍💻 Admin bilan aloqa")
async def support_handler(message: types.Message):
    await message.answer("👨‍💻 Admin: @admin_usernameringiz")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
