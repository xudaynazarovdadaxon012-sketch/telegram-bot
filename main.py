import os
import sqlite3
import logging
import asyncio
import io
import urllib.parse
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, BufferedInputFile, BotCommand, BotCommandScopeDefault
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from deep_translator import GoogleTranslator

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

# O'zgaruvchilar
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8898979946"))
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- DATABASE SETUP ---
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    joined_date TEXT
)
""")
conn.commit()

def add_user(user_id, username):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)", 
                   (user_id, username, today))
    conn.commit()

def get_stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    return total_users

# --- FSM STATES ---
class BotStates(StatesGroup):
    waiting_for_translate = State()
    waiting_for_image_prompt = State()
    waiting_for_ocr = State()
    waiting_for_shorten = State()

# --- HELPER FUNCTIONS ---
async def safe_translate(text: str, target: str = 'uz') -> str:
    try:
        translated = await asyncio.to_thread(
            GoogleTranslator(source='auto', target=target).translate, text
        )
        return translated
    except Exception as e:
        logging.error(f"Tarjima xatosi: {e}")
        return None

# --- KEYBOARDS ---
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 AI Rasm Generator"), KeyboardButton(text="abc Matn Tarjimon")],
            [KeyboardButton(text="🔍 Rasmdan Matn O'qish"), KeyboardButton(text="🔗 Havola Qisqartirish")],
            [KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )
    return kb

# --- HANDLERS ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    add_user(message.from_user.id, message.from_user.username)
    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "🤖 **Mega AI & Media Assistant** botiga xush kelibsiz.\n"
        "Quyidagi menyudan kerakli xizmatni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = get_stats()
        await message.answer(f"📊 <b>Admin Panel</b>\n\nJami foydalanuvchilar soni: <b>{total} ta</b>", parse_mode="HTML")
    else:
        await message.answer("❌ Siz admin emassiz.")

# 1. AI RASM GENERATOR
@dp.message(F.text == "🖼 AI Rasm Generator")
async def img_gen_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_prompt)
    await message.answer("🎨 Yaratmoqchi bo'lgan rasmingizni tasvirlab yozing (ingliz yoki o'zbek tilida):")

@dp.message(BotStates.waiting_for_image_prompt)
async def process_image_gen(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔄 AI rasm chizmoqda, bir oz kuting...")
    try:
        prompt_en = await safe_translate(message.text, target='en') or message.text
        encoded_prompt = urllib.parse.quote(prompt_en)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=30) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    input_file = BufferedInputFile(image_bytes, filename="ai_image.png")
                    await message.answer_photo(photo=input_file, caption=f"✨ <b>Natija:</b> {message.text}", parse_mode="HTML")
                    await wait_msg.delete()
                else:
                    await wait_msg.edit_text("❌ Rasm yaratishda xatolik yuz berdi. Qayta urinib ko'ring.")
    except Exception as e:
        logging.error(f"Image gen error: {e}")
        await wait_msg.edit_text("❌ Servisda xatolik bo'ldi.")
    finally:
        await state.clear()

# 2. REAL-TIME TARJIMON
@dp.message(F.text == "abc Matn Tarjimon")
async def translate_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_translate)
    await message.answer("🔤 Tarjima qilmoqchi bo'lgan matningizni yozib yuboring:")

@dp.message(BotStates.waiting_for_translate)
async def process_translate(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔄 Tarjima qilinmoqda...")
    try:
        translated_text = await safe_translate(message.text, target='uz')
        if translated_text:
            await wait_msg.edit_text(f"🇺🇿 **O'zbekcha Tarjima:**\n\n{translated_text}", parse_mode="Markdown")
        else:
            await wait_msg.edit_text("❌ Tarjima qilishda xatolik bo'ldi.")
    except Exception as e:
        logging.error(f"Tarjima xatosi: {e}")
        await wait_msg.edit_text("❌ Tarjima servisi bilan bog'lanishda xatolik bo'ldi.")
    finally:
        await state.clear()

# 3. RASMDAN MATN O'QISH (OCR)
@dp.message(F.text == "🔍 Rasmdan Matn O'qish")
async def ocr_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ocr)
    await message.answer("📷 Ichida matn bor rasmni yuboring:")

@dp.message(BotStates.waiting_for_ocr, F.photo)
async def process_ocr(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔍 Rasm tahlil qilinmoqda...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.ocr.space/parse/imageurl?apikey=helloworld&url={file_url}") as resp:
                data = await resp.json()
                parsed = data.get("ParsedResults")
                if parsed:
                    text = parsed[0].get("ParsedText", "")
                    if text.strip():
                        await wait_msg.edit_text(f"📝 **Rasm ichidagi matn:**\n\n`{text}`", parse_mode="Markdown")
                    else:
                        await wait_msg.edit_text("❌ Rasmda hech qanday matn topilmadi.")
                else:
                    await wait_msg.edit_text("❌ OCR servisi rasm matnini o'qiy olmadi.")
    except Exception as e:
        logging.error(f"OCR Error: {e}")
        await wait_msg.edit_text("❌ Rasmni o'qishda xatolik yuz berdi.")
    finally:
        await state.clear()

# 4. HAVOLA QISQARTIRISH
@dp.message(F.text == "🔗 Havola Qisqartirish")
async def shorten_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_shorten)
    await message.answer("🔗 Qisqartirmoqchi bo'lgan uzun havolangizni yuboring:")

@dp.message(BotStates.waiting_for_shorten)
async def process_shorten(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http"):
        url = "http://" + url
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://is.gd/api.php?format=json&url={urllib.parse.quote(url)}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    short_url = data.get("shorturl")
                    await message.answer(f"✅ **Qisqartirilgan havola:**\n{short_url}", parse_mode="Markdown")
                else:
                    await message.answer("❌ Havolani qisqartirishda xatolik bo'ldi.")
    except Exception as e:
        await message.answer("❌ Xato havola kiritildi yoki servis ishlamayapti.")
    finally:
        await state.clear()

# BOT STARTUP & BOT COMMANDS
async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="admin", description="Admin statistikasi")
    ], scope=BotCommandScopeDefault())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
