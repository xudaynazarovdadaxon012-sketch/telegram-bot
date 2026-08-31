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
from aiohttp import web
import qrcode
from deep_translator import GoogleTranslator

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Asosiy o'zgaruvchilar
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8898979946"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

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
cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    note_text TEXT,
    created_at TEXT
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
    return cursor.fetchone()[0]

def add_note_db(user_id, text):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO notes (user_id, note_text, created_at) VALUES (?, ?, ?)", (user_id, text, today))
    conn.commit()

def get_user_notes(user_id):
    cursor.execute("SELECT note_text, created_at FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
    return cursor.fetchall()

# --- FSM STATES ---
class BotStates(StatesGroup):
    waiting_for_ai = State()
    waiting_for_image_prompt = State()
    waiting_for_video_url = State()
    waiting_for_ocr = State()
    waiting_for_shorten = State()
    waiting_for_translate = State()
    waiting_for_qr = State()
    waiting_for_calc = State()
    waiting_for_weather = State()
    waiting_for_note = State()

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

# --- PREMIUM KEYBOARD ---
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="🤖 Sun'iy Intellekt (AI)"), KeyboardButton(text="🎨 AI Rasm Yaratish")],
            [KeyboardButton(text="📥 Video Yuklagich"), KeyboardButton(text="📄 Rasmdan Matn O'qish")],
            [KeyboardButton(text="📈 Kripto & Oltin"), KeyboardButton(text="🔗 Link Qisqartirish")],
            [KeyboardButton(text="abc Matn Tarjimon"), KeyboardButton(text="📲 QR-Kod Yaratish")],
            [KeyboardButton(text="🧮 Aqlli Kalkulyator"), KeyboardButton(text="🌤 Aniq Ob-havo")],
            [KeyboardButton(text="💎 Valyuta kurslari"), KeyboardButton(text="📝 Shaxsiy Eslatmalar")]
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
        f"💎 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "✨ <b>Mega AI & Premium Assistant</b> botiga xush kelibsiz.\n"
        "Nodir funksiyalar va qulayliklar menyusi pastda joylashgan 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = get_stats()
        await message.answer(f"👑 <b>Admin Panel</b>\n\n📊 Jami foydalanuvchilar: <b>{total} ta</b>", parse_mode="HTML")
    else:
        await message.answer("❌ Siz admin emassiz.")

# 1. SUN'IY INTELLEKT (AI CHAT)
@dp.message(F.text == "🤖 Sun'iy Intellekt (AI)")
async def ai_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ai)
    await message.answer("💬 **AI Assistent tayyor.** Savolingiz yoki topshirig'ingizni yozing:")

@dp.message(BotStates.waiting_for_ai)
async def process_ai(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🧠 AI o me'zoniy o'ylamoqda...")
    try:
        prompt_en = await safe_translate(message.text, target='en') or message.text
        encoded_prompt = urllib.parse.quote(prompt_en)
        url = f"https://text.pollinations.ai/{encoded_prompt}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                if resp.status == 200:
                    ai_res = await resp.text()
                    translated_res = await safe_translate(ai_res, target='uz') or ai_res
                    await wait_msg.edit_text(f"🤖 **AI Javobi:**\n\n{translated_res}")
                else:
                    await wait_msg.edit_text("❌ AI javob bera olmadi. Qayta urinib ko'ring.")
    except Exception as e:
        await wait_msg.edit_text("❌ AI servisi bilan bog'lanishda xatolik bo'ldi.")
    finally:
        await state.clear()

# 2. AI RASM YARATISH
@dp.message(F.text == "🎨 AI Rasm Yaratish")
async def img_gen_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_prompt)
    await message.answer("🎨 Tasvirlang (Masalan: *Qorli tog' tepasida tunda turgan chiroyli mashina*):")

@dp.message(BotStates.waiting_for_image_prompt)
async def process_image_gen(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🎨 Rasm chizilmoqda, kuting...")
    try:
        prompt_en = await safe_translate(message.text, target='en') or message.text
        encoded = urllib.parse.quote(prompt_en)
        image_url = f"https://image.pollinations.ai/prompt/{encoded}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=30) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    file = BufferedInputFile(image_bytes, filename="ai.png")
                    await message.answer_photo(photo=file, caption=f"✨ **Natija:** {message.text}")
                    await wait_msg.delete()
                else:
                    await wait_msg.edit_text("❌ Rasm yaratishda xatolik yuz berdi.")
    except Exception:
        await wait_msg.edit_text("❌ Rasm servisi javob bermadi.")
    finally:
        await state.clear()

# 3. VIDEO YUKLAGICH
@dp.message(F.text == "📥 Video Yuklagich")
async def video_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_video_url)
    await message.answer("📥 **TikTok / Instagram / YouTube** video havolasini yuboring:")

@dp.message(BotStates.waiting_for_video_url)
async def process_video(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔄 Video tahlil qilinmoqda...")
    try:
        url = urllib.parse.quote(message.text.strip())
        api_url = f"https://api.cobalt.tools/api/json"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {"url": message.text.strip()}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers, timeout=25) as resp:
                data = await resp.json()
                if data.get("url"):
                    await message.answer_video(video=data.get("url"), caption="✅ Vizual kontent yuklab olindi!")
                    await wait_msg.delete()
                else:
                    await wait_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havolani tekshiring.")
    except Exception:
        await wait_msg.edit_text("❌ Video yuklash servisida vaqtinchalik xatolik.")
    finally:
        await state.clear()

# 4. RASMDAN MATN O'QISH (OCR)
@dp.message(F.text == "📄 Rasmdan Matn O'qish")
async def ocr_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ocr)
    await message.answer("📷 Ichida matn bo'lgan rasmni yozuvsiz yuboring:")

@dp.message(BotStates.waiting_for_ocr, F.photo)
async def process_ocr(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔍 Matn aniqlanmoqda...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.ocr.space/parse/imageurl?apikey=helloworld&url={file_url}") as resp:
                data = await resp.json()
                parsed = data.get("ParsedResults")
                if parsed and parsed[0].get("ParsedText"):
                    await wait_msg.edit_text(f"📝 **Rasmdagi matn:**\n\n`{parsed[0].get('ParsedText')}`", parse_mode="Markdown")
                else:
                    await wait_msg.edit_text("❌ Rasmda matn aniqlanmadi.")
    except Exception:
        await wait_msg.edit_text("❌ OCR servisi xatosi.")
    finally:
        await state.clear()

# 5. KRIPTO & OLTIN
@dp.message(F.text == "📈 Kripto & Oltin")
async def crypto_rates(message: types.Message):
    wait_msg = await message.answer("🔄 Narxlar yangilanmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,gold&vs_currencies=usd") as resp:
                data = await resp.json()
                btc = data.get("bitcoin", {}).get("usd", "N/A")
                eth = data.get("ethereum", {}).get("usd", "N/A")
                bnb = data.get("binancecoin", {}).get("usd", "N/A")
                
                text = (
                    "📈 **Bozor Narxlari (USD):**\n\n"
                    f"🪙 **Bitcoin (BTC):** ${btc:,}\n"
                    f"🔷 **Ethereum (ETH):** ${eth:,}\n"
                    f"🟡 **Binance Coin (BNB):** ${bnb:,}\n"
                    "👑 **Oltin (XAU 1 oz):** ~$2,500+"
                )
                await wait_msg.edit_text(text, parse_mode="Markdown")
    except Exception:
        await wait_msg.edit_text("❌ Bozor narxlarini olishda xatolik.")

# 6. LINK QISQARTIRISH
@dp.message(F.text == "🔗 Link Qisqartirish")
async def shorten_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_shorten)
    await message.answer("🔗 Uzun havolani yuboring:")

@dp.message(BotStates.waiting_for_shorten)
async def process_shorten(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http"):
        url = "http://" + url
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://is.gd/api.php?format=json&url={urllib.parse.quote(url)}") as resp:
                data = await resp.json()
                if data.get("shorturl"):
                    await message.answer(f"✅ **Qisqartirilgan havola:**\n{data.get('shorturl')}")
                else:
                    await message.answer("❌ Qisqartirib bo'lmadi.")
    except Exception:
        await message.answer("❌ Noto'g'ri URL yoki servis ishlamayapti.")
    finally:
        await state.clear()

# 7. MATN TARJIMON
@dp.message(F.text == "abc Matn Tarjimon")
async def translate_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_translate)
    await message.answer("🔤 Tarjima qilmoqchi bo'lgan matnni kiriting:")

@dp.message(BotStates.waiting_for_translate)
async def process_translate(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔄 Tarjima qilinmoqda...")
    try:
        res = await safe_translate(message.text, target='uz')
        if res:
            await wait_msg.edit_text(f"🇺🇿 **O'zbekcha Tarjima:**\n\n{res}")
        else:
            await wait_msg.edit_text("❌ Tarjima xatoligi.")
    except Exception:
        await wait_msg.edit_text("❌ Tarjima servisi band.")
    finally:
        await state.clear()

# 8. QR-KOD YARATISH
@dp.message(F.text == "📲 QR-Kod Yaratish")
async def qr_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_qr)
    await message.answer("📲 QR-kodga aylantirish uchun matn yoki link yuboring:")

@dp.message(BotStates.waiting_for_qr)
async def process_qr(message: types.Message, state: FSMContext):
    try:
        img = qrcode.make(message.text)
        bio = io.BytesIO()
        bio.name = 'qrcode.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        file = BufferedInputFile(bio.read(), filename="qr.png")
        await message.answer_photo(photo=file, caption="✅ Tayyor QR-kod!")
    except Exception:
        await message.answer("❌ QR-kod yaratishda xatolik.")
    finally:
        await state.clear()

# 9. AQLLI KALKULYATOR
@dp.message(F.text == "🧮 Aqlli Kalkulyator")
async def calc_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_calc)
    await message.answer("🧮 Matematik ifodani yozing (Masalan: `(45 + 55) * 2 / 5`):")

@dp.message(BotStates.waiting_for_calc)
async def process_calc(message: types.Message, state: FSMContext):
    try:
        # Xavfsiz hisoblash
        allowed = set("0123456789+-*/(). ")
        if not set(message.text).issubset(allowed):
            await message.answer("❌ Faqat raqamlar va matematik belgilardan foydalaning.")
        else:
            result = eval(message.text, {"__builtins__": None}, {})
            await message.answer(f"🧮 **Natija:** `{result}`", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ Xato ifoda kiritildi.")
    finally:
        await state.clear()

# 10. ANIQ OB-HAVO
@dp.message(F.text == "🌤 Aniq Ob-havo")
async def weather_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_weather)
    await message.answer("🏙 Shahar nomini kiriting (Masalan: *Tashkent*, *Samarkand*):")

@dp.message(BotStates.waiting_for_weather)
async def process_weather(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("🔍 Qidirilmoqda...")
    try:
        city = urllib.parse.quote(message.text.strip())
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{city}?format=j1") as resp:
                data = await resp.json()
                curr = data["current_condition"][0]
                temp_c = curr["temp_C"]
                desc = curr["weatherDesc"][0]["value"]
                desc_uz = await safe_translate(desc, target='uz') or desc
                
                res_text = (
                    f"🌤 **{message.text.capitalize()} shahri ob-havosi:**\n\n"
                    f"🌡 Harorat: **{temp_c}°C**\n"
                    f"🌈 Holat: **{desc_uz}**\n"
                    f"💧 Namlik: **{curr['humidity']}%**\n"
                    f"💨 Shamol: **{curr['windspeedKmph']} km/h**"
                )
                await wait_msg.edit_text(res_text, parse_mode="Markdown")
    except Exception:
        await wait_msg.edit_text("❌ Shahar topilmadi yoki servis ishlamayapti.")
    finally:
        await state.clear()

# 11. VALYUTA KURSLARI
@dp.message(F.text == "💎 Valyuta kurslari")
async def currency_rates(message: types.Message):
    wait_msg = await message.answer("🔄 Markaziy Bank kurslari olinmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/") as resp:
                data = await resp.json()
                usd = next((item for item in data if item["Ccy"] == "USD"), None)
                eur = next((item for item in data if item["Ccy"] == "EUR"), None)
                rub = next((item for item in data if item["Ccy"] == "RUB"), None)
                
                res = (
                    "🏦 **O'zbekiston Markaziy Banki Valyuta Kurslari:**\n\n"
                    f"🇺🇸 **1 USD** = {usd['Rate']} so'm\n"
                    f"🇪🇺 **1 EUR** = {eur['Rate']} so'm\n"
                    f"🇷🇺 **1 RUB** = {rub['Rate']} so'm"
                )
                await wait_msg.edit_text(res, parse_mode="Markdown")
    except Exception:
        await wait_msg.edit_text("❌ Kurslarni olishda xatolik.")

# 12. SHAXSIY ESLATMALAR
@dp.message(F.text == "📝 Shaxsiy Eslatmalar")
async def notes_menu(message: types.Message, state: FSMContext):
    user_notes = get_user_notes(message.from_user.id)
    text = "📝 **Sizning oxirgi eslatmalaringiz:**\n\n"
    if user_notes:
        for i, (n_text, n_date) in enumerate(user_notes, 1):
            text += f"{i}. {n_text} _({n_date})_\n"
    else:
        text += "_Hali hech narsa saqlanmagan._\n"
    
    text += "\n✍️ Yangi eslatma saqlash uchun shunchaki matnni yozib yuboring:"
    await state.set_state(BotStates.waiting_for_note)
    await message.answer(text, parse_mode="Markdown")

@dp.message(BotStates.waiting_for_note)
async def process_note(message: types.Message, state: FSMContext):
    add_note_db(message.from_user.id, message.text)
    await message.answer("✅ Eslatrangiz muvaffaqiyatli saqlandi!")
    await state.clear()

# --- RENDER PORT PING SERVER ---
async def handle_ping(request):
    return web.Response(text="Bot runs successfully!")

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="admin", description="Admin statistikasi")
    ], scope=BotCommandScopeDefault())
    
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
