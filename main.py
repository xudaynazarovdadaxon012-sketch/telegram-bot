import asyncio
import logging
import os
from dotenv import load_dotenv

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@kanalingiz_usernamesi")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8898979946"))

# GitHub Pages-dagi miniapp.html manzili
WEBAPP_URL = os.getenv(
    "WEBAPP_URL", "https://xudaynazarovdadaxon012-sketch.github.io/telegram-bot/miniapp.html"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class AdminState(StatesGroup):
    waiting_for_broadcast = State()


ALL_USERS = set()
VIP_USERS = set()

GAMES_DATABASE = {
    # BEPUL O'YINLAR
    "nfs": {
        "title": "🏎 Need for Speed: Most Wanted (ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "minecraft": {
        "title": "⛏ Minecraft PE v1.20 (APK)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "pes": {
        "title": "⚽ eFootball PES 2024 (PPSSPP)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "subway": {
        "title": "🏃 Subway Surfers (MOD Money)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "tekken": {
        "title": "🥊 Tekken 6 (PSP ISO)",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "asphalt": {
        "title": "🚘 Asphalt 9: Legends",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    # VIP O'YINLAR
    "gta_lcs": {
        "title": "🚗 GTA: Liberty City Stories",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "gta_vcs": {
        "title": "🏙 GTA: Vice City Stories",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "god_of_war": {
        "title": "⚔ God of War: Ghost of Sparta",
        "file": "https://raw.githubusercontent.com/telegram/telegram-bot-sdk/master/README.md",
    },
    "mortal_kombat": {
        "title": "🐉 Mortal Kombat Unchained",
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


def get_main_menu(user_id: int):
    buttons = [
        [
            KeyboardButton(text="🎮 O'yinlar Katalogi"),
            KeyboardButton(text="💎 VIP Bo'lim"),
        ],
        [
            KeyboardButton(text="🔍 O'yin Qidirish"),
            KeyboardButton(text="📊 Statistika"),
        ],
        [KeyboardButton(text="👨‍💻 Qo'llab-quvvatlash")],
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙ Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Rasmiy Kanalimiz",
                    url=f"https://t.me/{CHANNEL_ID.replace('@', '')}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Obunani Tasdiqlash", callback_data="check_sub"
                )
            ],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id)

    if not await check_subscription(user_id):
        await message.answer(
            f"Assalomu alaykum <b>{message.from_user.first_name}</b>!\n\n"
            "Botdan to'liq foydalanish uchun kanalimizga obuna bo'ling:",
            parse_mode="HTML",
            reply_markup=get_sub_keyboard(),
        )
        return

    await message.answer(
        f"🔥 <b>Game Hub Store</b> botiga xush kelibsiz!\n\n"
        "O'zingizga kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=get_main_menu(user_id),
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!", reply_markup=get_main_menu(user_id)
        )
    else:
        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True
        )


@dp.message(F.text == "🎮 O'yinlar Katalogi")
async def free_games_handler(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏎 Need for Speed", callback_data="game_nfs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛏ Minecraft PE", callback_data="game_minecraft"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚽ eFootball PES 2024", callback_data="game_pes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏃 Subway Surfers", callback_data="game_subway"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥊 Tekken 6 ISO", callback_data="game_tekken"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚘 Asphalt 9", callback_data="game_asphalt"
                )
            ],
        ]
    )
    await message.answer(
        "🎮 <b>BEPUL O'YINLAR KATALOGI:</b>", parse_mode="HTML", reply_markup=kb
    )


@dp.message(F.text == "💎 VIP Bo'lim")
async def vip_games_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id in VIP_USERS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚗 GTA Liberty City", callback_data="game_gta_lcs"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏙 GTA Vice City", callback_data="game_gta_vcs"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚔ God of War", callback_data="game_god_of_war"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🐉 Mortal Kombat",
                        callback_data="game_mortal_kombat",
                    )
                ],
            ]
        )
        await message.answer(
            "💎 <b>Siz VIP a'zosiz!</b> O'yinni tanlang:",
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
            "💎 <b>VIP Eksklyuziv O'yinlar Paketini ochish uchun obuna bo'ling:</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )


@dp.callback_query(F.data.startswith("game_"))
async def send_game_file(callback: types.CallbackQuery):
    await callback.answer("⚡ Fayl yuborilmoqda...")
    game_key = callback.data.replace("game_", "")
    game_data = GAMES_DATABASE.get(game_key)

    if game_data:
        await callback.message.answer_document(
            document=game_data["file"],
            caption=f"✅ <b>{game_data['title']}</b> fayli tayyor!",
            parse_mode="HTML",
        )


@dp.message(F.text == "🔍 O'yin Qidirish")
async def search_prompt(message: types.Message):
    await message.answer(
        "🔎 Qidirmoqchi bo'lgan o'yin nomini yozib yuboring (Masalan: <i>GTA</i> yoki <i>PES</i>):",
        parse_mode="HTML",
    )


@dp.message(F.text & ~F.text.startswith("/"))
async def auto_search_game(message: types.Message):
    query = message.text.lower().strip()

    if query in [
        "🎮 o'yinlar katalogi",
        "💎 vip bo'lim",
        "📊 statistika",
        "👨‍💻 qo'llab-quvvatlash",
        "⚙ admin panel",
    ]:
        return

    found_games = []
    for key, data in GAMES_DATABASE.items():
        if query in data["title"].lower():
            found_games.append(
                [
                    InlineKeyboardButton(
                        text=data["title"], callback_data=f"game_{key}"
                    )
                ]
            )

    if found_games:
        kb = InlineKeyboardMarkup(inline_keyboard=found_games)
        await message.answer(
            f'🎯 <b>Natijalar ("{message.text}"):</b>',
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await message.answer(
            "❌ Baza bo'yicha bunday o'yin topilmadi. Katalogdan qidirib ko'ring."
        )


@dp.message(F.text == "📊 Statistika")
async def stats_handler(message: types.Message):
    total_users = len(ALL_USERS)
    vip_count = len(VIP_USERS)

    app_url = f"{WEBAPP_URL}?total={total_users}&vip={vip_count}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📈 Jonli Animatsiyali Diagramma",
                    web_app=WebAppInfo(url=app_url),
                )
            ]
        ]
    )

    await message.answer(
        f"📊 <b>GAME HUB STATISTIKASI:</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total_users}</b> ta\n"
        f"💎 VIP obunachilar: <b>{vip_count}</b> ta\n\n"
        f"👇 0 dan osadigan animatsiyali diagrammani ko'rish uchun pastdagi tugmani bosing:",
        parse_mode="HTML",
        reply_markup=kb,
    )


@dp.message(F.text == "⚙ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Xabar tarqatish (Rassilka)",
                    callback_data="start_broadcast",
                )
            ]
        ]
    )
    await message.answer("⚙ <b>Admin Boshqaruv Paneli:</b>", reply_markup=kb)


@dp.callback_query(F.data == "start_broadcast")
async def broadcast_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user.id == ADMIN_ID:
        await callback.message.answer(
            "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:"
        )
        await state.set_state(AdminState.waiting_for_broadcast)


@dp.message(AdminState.waiting_for_broadcast)
async def perform_broadcast(message: types.Message, state: FSMContext):
    count = 0
    for u_id in ALL_USERS:
        try:
            await message.send_copy(chat_id=u_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(
        f"✅ Xabar muvaffaqiyatli {count} ta foydalanuvchiga yuborildi!"
    )
    await state.clear()


@dp.message(F.text == "👨‍💻 Qo'llab-quvvatlash")
async def support_handler(message: types.Message):
    await message.answer("👨‍‍💻 Admin aloqa: @admin_usernameringiz")


@dp.callback_query(F.data == "buy_vip_50")
async def send_invoice(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP Obuna",
        description="Eksklyuziv top o'yinlarni yuklab olish.",
        payload="vip_sub_50_stars",
        currency="XTR",
        prices=[LabeledPrice(label="VIP Pass", amount=50)],
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    VIP_USERS.add(message.from_user.id)
    await message.answer("🎉 VIP obunangiz muvaffaqiyatli faollashtirildi!")


# --- RENDER UCHUN VEB-SERVER (PORT SINOVIDAN O'TISH UCHUN) ---
async def handle_ping(request):
    return web.Response(text="Bot ishlayapti va port faol!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    logging.basicConfig(level=logging.INFO)
    # Veb-server va botni bir vaqtda ishga tushiramiz
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
