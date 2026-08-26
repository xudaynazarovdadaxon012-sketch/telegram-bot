import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- SOZLAMALAR ---
# 1. @BotFather bergan Bot Tokeningizni kiriting
BOT_TOKEN = "8760162640:AAH-zUL0Avfgdz5fHsADPjEW-1xUVS0m4-s"

# 2. GitHub Pages taqdim etgan rasmiy havola (miniapp.html yoki index.html bo'lsin)
MINI_APP_URL = "https://xudaynazarovdadaxon012-sketch.github.io/telegram-bot/miniapp.html"

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# --- 1. /start BUYRUG'I HANDLERI ---
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_name = message.from_user.first_name
    
    # Mini App tugmasi
    keyboard = InlineKeyboardMarkup()
    tma_button = InlineKeyboardButton(
        text="🌟 Interactive Mini App", 
        web_app=WebAppInfo(url=MINI_APP_URL)
    )
    keyboard.add(tma_button)

    welcome_text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        f"Botimizga xush kelibsiz. Animatsiyali va zamonaviy menyuni ochish uchun "
        f"quyidagi tugmani bosing:"
    )

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")


# --- 2. MINI APP'DAN KELGAN MA'LUMOTLARNI QABUL QILISH ---
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def handle_miniapp_data(message: types.Message):
    received_data = message.web_app_data.data
    user_name = message.from_user.first_name

    # Ob-havo
    if received_data == 'A:WEATHER':
        await message.answer(
            f"🌤 <b>{user_name}</b>, bugungi ob-havo ma'lumoti:\n\n"
            f"📍 Toshkent: +28°C, Ochiq havo\n"
            f"💨 Shamol: 4 m/s\n"
            f"💦 Namlik: 35%",
            parse_mode="HTML"
        )

    # Valyuta kursi
    elif received_data == 'A:CURRENCY':
        await message.answer(
            f"🔱 <b>{user_name}</b>, Markaziy Bank kursi:\n\n"
            f"💵 1 USD = 12 650 so'm\n"
            f"💶 1 EUR = 13 800 so'm\n"
            f"💷 1 RUB = 142 so'm",
            parse_mode="HTML"
        )

    # Eslatma qo'shish
    elif received_data == 'A:ADD_REMINDER':
        await message.answer(
            f"📝 <b>Eslatma yaratish bo'limi:</b>\n\n"
            f"Iltimos, eslatma matni va vaqtini yozib yuboring:\n"
            f"<i>Masalan: Bugun 20:00 dars qilish</i>",
            parse_mode="HTML"
        )

    # O'yinlar menyusi
    elif received_data == 'A:GAMES':
        game_keyboard = InlineKeyboardMarkup(row_width=2)
        btn1 = InlineKeyboardButton(text="🎲 Zabon (Dice)", callback_data="game_dice")
        btn2 = InlineKeyboardButton(text="🎯 Darts", callback_data="game_dart")
        btn3 = InlineKeyboardButton(text="🎰 Slot", callback_data="game_slots")
        btn4 = InlineKeyboardButton(text="⚽ Penalti", callback_data="game_football")
        game_keyboard.add(btn1, btn2, btn3, btn4)

        await message.answer(
            f"🎮 <b>{user_name}</b>, o'yinni tanlang:",
            reply_markup=game_keyboard,
            parse_mode="HTML"
        )


# --- 3. INLINE O'YIN TUGMALARI BOSILGANDA ---
@dp.callback_query_handler(lambda c: c.data.startswith('game_'))
async def process_game(callback_query: types.CallbackQuery):
    game_type = callback_query.data
    chat_id = callback_query.from_user.id

    if game_type == "game_dice":
        await bot.send_dice(chat_id, emoji="🎲")
    elif game_type == "game_dart":
        await bot.send_dice(chat_id, emoji="🎯")
    elif game_type == "game_slots":
        await bot.send_dice(chat_id, emoji="🎰")
    elif game_type == "game_football":
        await bot.send_dice(chat_id, emoji="⚽")

    await callback_query.answer()


# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == '__main__':
    print("Bot muvaffaqiyatli ishga tushirildi...")
    executor.start_polling(dp, skip_updates=True)
