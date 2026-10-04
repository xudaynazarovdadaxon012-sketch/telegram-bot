import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    FSInputFile
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Homiy kanal ID si
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/telegram")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: BOT_TOKEN topilmadi! Render yoki .env faylini tekshiring.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1-martalik demo tarixini xotirada saqlash
played_demos = {}

# O'yinlar va ilovalar bazasi
GAMES_DB = {
    "cyber_strike": {
        "title": "Cyber Strike Online (APK)",
        "category": "🎮 O'yinlar",
        "size": "45 MB",
        "desc": "Android uchun eng yaxshi otishma o'yini. Offlayn va Onlayn rejimlar mavjud.",
        "file_id": "BAACAgIAAxkBAAE...",  # Telegram file_id yoki mahalliy fayl yo'li: "files/cyber_strike.apk"
        "local_file": "files/cyber_strike.apk"  # Agar kompyuterdan/serverdan yuklansa
    },
    "shadow_runner": {
        "title": "Shadow Runner RPG (APK)",
        "category": "🎮 O'yinlar",
        "size": "85 MB",
        "desc": "Ochiq dunyodagi fantastik RPG o'yini.",
        "file_id": None,
        "local_file": "files/shadow_runner.apk"
    }
}

# --- MAJBURITY OBUNANI TEKSHIRISH (Force Subscribe) ---
async def check_subscription(user_id: int) -> bool:
    if not CHANNEL_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return True

def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# --- MENYULAR ---
def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 O'yinlar", callback_data="cat:games"),
                InlineKeyboardButton(text="📱 Ilovalar", callback_data="cat:apps")
            ],
            [
                InlineKeyboardButton(text="🔍 Qidiruv ko'rsatmasi", callback_data="search_help"),
                InlineKeyboardButton(text="⭐ Premium", callback_data="premium_info")
            ]
        ]
    )

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Obuna tekshirish
    if not await check_subscription(user_id):
        await message.answer(
            "⚠️ **Botdan foydalanish uchun rasmiy kanalimizga obuna bo'ling!**\n\n"
            "Obuna bo'lgach, '✅ Obunani tekshirish' tugmasini bosing.",
            reply_markup=get_sub_keyboard(),
            parse_mode="Markdown"
        )
        return

    await message.answer(
        f"👋 Salom **{message.from_user.first_name}**!\n"
        f"**ILOVAXUZ** uslubidagi rasmiy o'yinlar va ilovalar botiga xush kelibsiz!\n\n"
        f"Kerakli bo'limni tanlang yoki shunchaki o'yin nomini chatga yozib qidiring (masalan: `Cyber`):",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Obunangiz tasdiqlandi! Asosiy menyu:",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# Kategoriyalar
@dp.callback_query(F.data == "cat:games")
async def show_games_list(callback: CallbackQuery):
    buttons = []
    for game_id, game in GAMES_DB.items():
        buttons.append([InlineKeyboardButton(text=f"📂 {game['title']}", callback_data=f"view:{game_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    
    await callback.message.edit_text(
        "📱 **Mavjud o'yinlar ro'yxati:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Asosiy menyu:", reply_markup=get_main_keyboard())

# O'yin kartochkasini ko'rsatish
@dp.callback_query(F.data.startswith("view:"))
async def view_item(callback: CallbackQuery):
    game_id = callback.data.split(":")[1]
    game = GAMES_DB.get(game_id)
    user_id = callback.from_user.id

    if not game:
        await callback.answer("Fayl topilmadi!", show_alert=True)
        return

    has_played = game_id in played_demos.get(user_id, [])
    demo_btn_text = "🔒 Demo ishlatilgan" if has_played else "🎲 1-martalik Demo"
    demo_cb = "demo_used" if has_played else f"demo:{game_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Yuklab olish (APK)", callback_data=f"download:{game_id}")],
            [InlineKeyboardButton(text=demo_btn_text, callback_data=demo_cb)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cat:games")]
        ]
    )

    caption = (
        f"📱 **{game['title']}**\n\n"
        f"📁 Kategoriyasi: {game['category']}\n"
        f"💾 Hajmi: {game['size']}\n\n"
        f"📝 {game['desc']}"
    )

    await callback.message.edit_text(caption, reply_markup=keyboard, parse_mode="Markdown")

# 1-martalik Instant Demo rejimi
@dp.callback_query(F.data.startswith("demo:"))
async def start_demo(callback: CallbackQuery):
    game_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Cheklovni qayd etish
    if user_id not in played_demos:
        played_demos[user_id] = []
    played_demos[user_id].append(game_id)

    demo_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚔️ Jang qilish", callback_data=f"demo_act:{game_id}:fight"),
                InlineKeyboardButton(text="🏃 Qochish", callback_data=f"demo_act:{game_id}:run")
            ]
        ]
    )

    await callback.message.edit_text(
        f"🕹 **{GAMES_DB[game_id]['title']} (1-Martalik Demo)**\n\n"
        f"Dushman paydo bo'ldi! Qaysi harakatni tanlaysiz? (Sinov imkoniyatingiz 1 ta):",
        reply_markup=demo_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("demo_act:"))
async def process_demo_action(callback: CallbackQuery):
    _, game_id, act = callback.data.split(":")
    
    res = "🔥 Ajoyib g'alaba! O'yin sizga mos keladi." if act == "fight" else "💨 Qochib qutuldingiz!"

    end_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 To'liq APK faylni yuklab olish", callback_data=f"download:{game_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cat:games")]
        ]
    )

    await callback.message.edit_text(
        f"🎮 **Demo Natijasi:**\n{res}\n\n"
        f"⚠️ *Sizning 1 martalik bepul sinov huquqingiz tugadi. To'liq o'yinni yuklab oling!*",
        reply_markup=end_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "demo_used")
async def demo_used_alert(callback: CallbackQuery):
    await callback.answer("❌ Siz bu o'yinning 1 martalik demosidan foydalanib bo'lgansiz!", show_alert=True)

# APK faylini Chatga yuborish (Download)
@dp.callback_query(F.data.startswith("download:"))
async def send_apk_file(callback: CallbackQuery):
    game_id = callback.data.split(":")[1]
    game = GAMES_DB.get(game_id)

    await callback.answer("⏳ APK fayli yuborilmoqda, kuting...")
    await callback.message.answer(f"⏳ **{game['title']}** fayli yuklanmoqda...")

    try:
        # 1-variant: Telegram file_id orqali (juda tez yuboradi)
        if game.get("file_id"):
            await callback.message.answer_document(
                document=game["file_id"],
                caption=f"✅ **{game['title']}**\n\n@SizningBotKanaliz orqali yuklab olindi."
            )
        # 2-variant: Mahalliy fayl orqali
        elif os.path.exists(game.get("local_file", "")):
            document = FSInputFile(game["local_file"])
            await callback.message.answer_document(
                document=document,
                caption=f"✅ **{game['title']}**\n\n@SizningBotKanaliz orqali yuklab olindi."
            )
        else:
            await callback.message.answer(
                f"🔗 Fayl serverda tayyorlanmoqda. Doimiy havola: https://example.com/downloads/{game_id}.apk"
            )
    except Exception as e:
        logging.error(f"Fayl yuborishda xato: {e}")
        await callback.message.answer("❌ Faylni yuborishda xatolik yuz berdi.")

# MATNLI QIDIRUV (Foydalanuvchi qidirsa)
@dp.message(F.text)
async def search_game(message: types.Message):
    query = message.text.lower().strip()
    results = []

    for game_id, game in GAMES_DB.items():
        if query in game["title"].lower() or query in game["desc"].lower():
            results.append([InlineKeyboardButton(text=f"📱 {game['title']}", callback_data=f"view:{game_id}")])

    if results:
        await message.answer(
            f"🔍 **'{query}' bo'yicha topilgan natijalar:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=results),
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"😔 Kechirasiz, '{query}' bo'yicha hech narsa topilmadi.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
