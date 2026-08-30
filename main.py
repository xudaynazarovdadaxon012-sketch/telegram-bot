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
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, 
    CallbackQuery, BufferedInputFile, BotCommand, BotCommandScopeDefault
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import ClientSession, ClientTimeout
import aiohttp
import qrcode

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "8760162640:AAHCVZH2bz5XIaVszG6OwJo2V2-tnuzPWWA")
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
    created_at TEXT
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

# --- FSM STATES ---
class BotStates(StatesGroup):
    waiting_for_note = State()
    waiting_for_qr = State()
    waiting_for_ai = State()
    waiting_for_image_prompt = State()
    waiting_for_shorten = State()
    waiting_for_translate = State()
    waiting_for_broadcast = State()

# --- BOT COMMANDS MENU ---
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Qayta ishga tushirish"),
        BotCommand(command="menu", description="📱 Asosiy menyu"),
        BotCommand(command="miniapp", description="🎮 O'yinlar Hub (Mini App)"),
        BotCommand(command="ai", description="🤖 ChatGPT (AI Chat)"),
        BotCommand(command="draw", description="🎨 AI Rasm Chizish"),
        BotCommand(command="ocr", description="📄 Rasmdan matnni o'qish"),
        BotCommand(command="downloader", description="📥 TikTok / Instagram Video"),
        BotCommand(command="crypto", description="📈 Crypto & Gold Narxlari"),
        BotCommand(command="shorten", description="🔗 Link Qisqartirish"),
        BotCommand(command="qr", description="📲 QR-kod Generatori"),
        BotCommand(command="help", description="ℹ️ Yordam")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

# --- MAIN KEYBOARD ---
def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎮 Mini App (O'yinlar Hub)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/miniapp.html"))],
            [types.KeyboardButton(text="🤖 Sun'iy Intellekt (AI)"), types.KeyboardButton(text="🎨 AI Rasm Yaratish")],
            [types.KeyboardButton(text="📥 Video Yuklagich"), types.KeyboardButton(text="📄 Rasmdan Matn O'qish")],
            [types.KeyboardButton(text="📈 Kripto & Oltin"), types.KeyboardButton(text="🔗 Link Qisqartirish")],
            [types.KeyboardButton(text="🔤 Matn Tarjimon"), types.KeyboardButton(text="📲 QR-Kod Yaratish")],
            [types.KeyboardButton(text="🧮 Aqlli Kalkulyator"), types.KeyboardButton(text="🌤 Aniq Ob-havo")],
            [types.KeyboardButton(text="💎 Valyuta kurslari"), types.KeyboardButton(text="📝 Shaxsiy Eslatmalar")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
@dp.message(Command("menu"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Foydalanuvchi"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)", 
                   (user_id, username, now))
    conn.commit()

    await message.answer(
        f"👑 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
        f"🚀 **Ultra-Premium Flagship Multi-Bot** tizimiga xush kelibsiz.\n"
        f"Barcha funksiyalardan foydalanish uchun quyidagi tugmalardan birini bosing 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# --- 1. AI CHATBOT (ChatGPT) ---
@dp.message(Command("ai"))
@dp.message(F.text == "🤖 Sun'iy Intellekt (AI)")
async def ai_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ai)
    await message.answer("🧠 **AI Yordamchi:**\nIstalgan savolingizni yozib yuboring:", parse_mode="Markdown")

@dp.message(BotStates.waiting_for_ai)
async def process_ai(message: types.Message, state: FSMContext):
    msg = await message.answer("🔄 _AI o'ylamoqda..._")
   try:
        url = f"https://text.pollinations.ai/{urllib.parse.quote(message.text)}"
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    reply = await resp.text()
                    await msg.edit_text(f"🤖 **AI Javobi:**\n\n{reply}")
                else:
                    await msg.edit_text("❌ AI javob bera olmadi, qayta urinib ko'ring.")
    except Exception:
        await msg.edit_text("❌ AI servisi bilan bog'lanishda xatolik bo'ldi.")
    await state.clear()

# --- 2. AI RASM GENERATORI (Text-to-Image) ---
@dp.message(Command("draw"))
@dp.message(F.text == "🎨 AI Rasm Yaratish")
async def draw_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_prompt)
    await message.answer("🎨 **AI Rasm Generator:**\nYaratmoqchi bo'lgan rasmingizni inglizcha matnda tasvirlab yuboring (Masalan: _A futuristic car in Tashkent, 8k resolution_):", parse_mode="Markdown")

@dp.message(BotStates.waiting_for_image_prompt)
async def process_draw(message: types.Message, state: FSMContext):
    msg = await message.answer("🎨 _Rasm chizilmoqda, kuting..._")
    try:
        prompt_encoded = urllib.parse.quote(message.text)
        img_url = f"https://pollinations.ai/p/{prompt_encoded}?width=1024&height=1024&seed=42"
        await message.answer_photo(photo=img_url, caption=f"✨ **AI tomonidan chizilgan rasm!**\n\n📝 **Prompt:** _{message.text}_", parse_mode="Markdown")
        await msg.delete()
    except Exception:
        await msg.edit_text("❌ Rasm yaratishda xatolik yuz berdi.")
    await state.clear()

# --- 3. KRIPTOVALYUTA VA OLTIN KURSLARI ---
@dp.message(Command("crypto"))
@dp.message(F.text == "📈 Kripto & Oltin")
async def get_crypto_prices(message: types.Message):
    msg = await message.answer("🔄 _Bozor narxlari yuklanmoqda..._")
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network,gold&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                btc = data.get("bitcoin", {}).get("usd", "N/A")
                eth = data.get("ethereum", {}).get("usd", "N/A")
                ton = data.get("the-open-network", {}).get("usd", "N/A")

                text = (
                    "📈 **Jahon Bozori Real-Time Narxlari:**\n\n"
                    f"🪙 **Bitcoin (BTC):** ${btc:,}\n"
                    f"🔷 **Ethereum (ETH):** ${eth:,}\n"
                    f"💎 **TON Coin (TON):** ${ton}\n\n"
                    f"⚡ *Ma'lumotlar avtomatik yangilanadi.*"
                )
                await msg.edit_text(text, parse_mode="Markdown")
    except Exception:
        await msg.edit_text("❌ Narxlarni olishda xatolik yuz berdi.")

# --- 4. LINK QISQARTIRISH (URL Shortener) ---
@dp.message(Command("shorten"))
@dp.message(F.text == "🔗 Link Qisqartirish")
async def shorten_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_shorten)
    await message.answer("🔗 Qisqartirmoqchi bo'lgan uzun havolangizni yuboring:")

@dp.message(BotStates.waiting_for_shorten)
async def process_shorten(message: types.Message, state: FSMContext):
    try:
        api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(message.text)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                short_url = await resp.text()
                await message.answer(f"✅ **Qisqartirilgan havola:**\n\n👉 {short_url}", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ Havolani qisqartirishda xatolik bo'ldi.")
    await state.clear()

# --- 5. REAL-TIME TARJIMON ---
@dp.message(F.text == "🔤 Matn Tarjimon")
async def translate_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_translate)
    await message.answer("🔤 Tarjima qilmoqchi bo'lgan matningizni yozib yuboring:")

@dp.message(BotStates.waiting_for_translate)
async def process_translate(message: types.Message, state: FSMContext):
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(message.text)}&langpair=autodetect|uz"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                trans = data.get("responseData", {}).get("translatedText", "Tarjima topilmadi.")
                await message.answer(f"🇺🇿 **O'zbekcha Tarjima:**\n\n{trans}")
    except Exception:
        await message.answer("❌ Tarjimada xatolik yuz berdi.")
    await state.clear()

# --- 6. RASMDAN MATN O'QISH (OCR API) ---
@dp.message(Command("ocr"))
@dp.message(F.text == "📄 Rasmdan Matn O'qish")
async def ocr_prompt(message: types.Message):
    await message.answer("📄 Ichida matni bor rasmni yuboring (Skrinshot yoki hujjat rasmi):")

@dp.message(F.photo)
async def process_ocr(message: types.Message):
    msg = await message.answer("📄 _Rasm ichidagi matn o'qilmoqda..._")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        ocr_api = f"https://api.ocr.space/parse/imageurl?apikey=helloworld&url={file_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(ocr_api) as resp:
                data = await resp.json()
                parsed = data.get("ParsedResults", [])
                if parsed:
                    text = parsed[0].get("ParsedText", "Matn aniqlanmadi.")
                    await msg.edit_text(f"📝 **Rasmdan aniqlangan matn:**\n\n`{text}`", parse_mode="Markdown")
                else:
                    await msg.edit_text("❌ Rasmda hech qanday matn topilmadi.")
    except Exception:
        await msg.edit_text("❌ Rasmni qayta ishlashda xatolik bo'ldi.")

# --- VIDEO YUKLAGICH & QR CODE ---
@dp.message(Command("downloader"))
@dp.message(F.text == "📥 Video Yuklagich")
async def downloader_prompt(message: types.Message):
    await message.answer("📥 **Instagram Reels** yoki **TikTok** video havolasini yuboring:")

@dp.message(F.text.contains("instagram.com") | F.text.contains("tiktok.com"))
async def download_video(message: types.Message):
    msg = await message.answer("🔄 _Video yuklanmoqda..._")
    try:
        url = f"https://api.cobalt.tools/api/json"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {"url": message.text}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                video_url = data.get("url")
                if video_url:
                    await message.answer_video(video=video_url, caption="✅ **Video yuklandi!**")
                    await msg.delete()
                else:
                    await msg.edit_text("❌ Videoni yuklab bo'lmadi.")
    except Exception:
        await msg.edit_text("❌ Yuklashda xatolik bo'ldi.")

@dp.message(Command("qr"))
@dp.message(F.text == "📲 QR-Kod Yaratish")
async def qr_prompt(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_qr)
    await message.answer("📲 Matn yoki havola yuboring:")

@dp.message(BotStates.waiting_for_qr)
async def generate_qr(message: types.Message, state: FSMContext):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(message.text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    
    file = BufferedInputFile(bio.read(), filename="qrcode.png")
    await message.answer_photo(photo=file, caption="✅ **QR-kodingiz tayyor!**", parse_mode="Markdown")
    await state.clear()

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Broadcast Yuborish", callback_data="admin_broadcast")]
        ])
        await message.answer(f"⚙️ **Admin Panel**\n\n📊 Jami foydalanuvchilar: **{count} ta**", reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer("❌ Siz admin emassiz!")

@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_broadcast)
    await call.message.answer("📢 Yuboriladigan xabarni kiriting:")
    await call.answer()

@dp.message(BotStates.waiting_for_broadcast)
async def send_broadcast(message: types.Message, state: FSMContext):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    sent = 0
    for u in users:
        try:
            await bot.send_message(u[0], message.text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Xabar **{sent}** ta foydalanuvchiga yuborildi!")
    await state.clear()

# --- KALKULYATOR, OB-HAVO, VALYUTA, ESLATMALAR ---
user_calc = {}

def get_calc_keyboard(expr="0"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📊 Disp: {expr}", callback_data="calc_noop")],
        [InlineKeyboardButton(text="🧹 C", callback_data="calc_clear"), InlineKeyboardButton(text="(", callback_data="calc_("), InlineKeyboardButton(text=")", callback_data="calc_)"), InlineKeyboardButton(text="÷", callback_data="calc_/")],
        [InlineKeyboardButton(text="7", callback_data="calc_7"), InlineKeyboardButton(text="8", callback_data="calc_8"), InlineKeyboardButton(text="9", callback_data="calc_9"), InlineKeyboardButton(text="×", callback_data="calc_*")],
        [InlineKeyboardButton(text="4", callback_data="calc_4"), InlineKeyboardButton(text="5", callback_data="calc_5"), InlineKeyboardButton(text="6", callback_data="calc_6"), InlineKeyboardButton(text="-", callback_data="calc_-")],
        [InlineKeyboardButton(text="1", callback_data="calc_1"), InlineKeyboardButton(text="2", callback_data="calc_2"), InlineKeyboardButton(text="3", callback_data="calc_3"), InlineKeyboardButton(text="+", callback_data="calc_+")],
        [InlineKeyboardButton(text="0", callback_data="calc_0"), InlineKeyboardButton(text=".", callback_data="calc_."), InlineKeyboardButton(text="🧮 =", callback_data="calc_eval")]
    ])

@dp.message(F.text == "🧮 Aqlli Kalkulyator")
async def show_calculator(message: types.Message):
    user_calc[message.from_user.id] = ""
    await message.answer("🧮 **Aqlli Kalkulyator:**", reply_markup=get_calc_keyboard("0"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("calc_"))
async def calc_callback(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.replace("calc_", "")
    current = user_calc.get(user_id, "")

    if action == "noop":
        await call.answer()
        return
    elif action == "clear":
        current = ""
    elif action == "eval":
        try:
            safe_expr = current.replace("×", "*").replace("÷", "/")
            current = str(eval(safe_expr))
        except Exception:
            current = "Xatolik"
    else:
        char = "×" if action == "*" else ("÷" if action == "/" else action)
        current += char

    user_calc[user_id] = current
    disp = current if current != "" else "0"
    try:
        await call.message.edit_reply_markup(reply_markup=get_calc_keyboard(disp))
    except Exception:
        pass
    await call.answer()

CITIES = {
    "toshkent": ("Toshkent", 41.2995, 69.2401), "andijon": ("Andijon", 40.7821, 72.3442),
    "fargona": ("Farg'ona", 40.3842, 71.7843), "namangan": ("Namangan", 41.0011, 71.6683),
    "samarqand": ("Samarqand", 39.6542, 66.9597), "buxoro": ("Buxoro", 39.7747, 64.4286),
    "xorazm": ("Urganch", 41.5500, 60.6333), "navoiy": ("Navoiy", 40.0844, 65.3792),
    "qashqadaryo": ("Qarshi", 38.8605, 65.7899), "surxondaryo": ("Termiz", 37.2242, 67.2783),
    "jizzax": ("Jizzax", 40.1158, 67.8422), "sirdaryo": ("Guliston", 40.4897, 68.7842),
    "nukus": ("Nukus", 42.4603, 59.6166)
}

@dp.message(F.text == "🌤 Aniq Ob-havo")
async def show_weather_cities(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Toshkent", callback_data="w_toshkent"), InlineKeyboardButton(text="📍 Andijon", callback_data="w_andijon")],
        [InlineKeyboardButton(text="📍 Farg'ona", callback_data="w_fargona"), InlineKeyboardButton(text="📍 Namangan", callback_data="w_namangan")],
        [InlineKeyboardButton(text="📍 Samarqand", callback_data="w_samarqand"), InlineKeyboardButton(text="📍 Buxoro", callback_data="w_buxoro")],
        [InlineKeyboardButton(text="📍 Xorazm", callback_data="w_xorazm"), InlineKeyboardButton(text="📍 Navoiy", callback_data="w_navoiy")],
        [InlineKeyboardButton(text="📍 Qashqadaryo", callback_data="w_qashqadaryo"), InlineKeyboardButton(text="📍 Surxondaryo", callback_data="w_surxondaryo")],
        [InlineKeyboardButton(text="📍 Jizzax", callback_data="w_jizzax"), InlineKeyboardButton(text="📍 Sirdaryo", callback_data="w_sirdaryo")],
        [InlineKeyboardButton(text="📍 Qoraqalpog'iston", callback_data="w_nukus")]
    ])
    await message.answer("🌤 **Kerakli hududni tanlang:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("w_"))
async def get_real_weather(call: CallbackQuery):
    city_key = call.data.replace("w_", "")
    if city_key in CITIES:
        name, lat, lon = CITIES[city_key]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    curr = data.get("current_weather", {})
                    temp = curr.get("temperature", "N/A")
                    wind = curr.get("windspeed", "N/A")
                    await call.message.answer(
                        f"🌤 **{name} bo'yicha Ob-havo:**\n\n🌡 Harorat: **{temp}°C**\n💨 Shamol: **{wind} km/h**",
                        parse_mode="Markdown"
                    )
        except Exception:
            await call.message.answer("Ob-havoni yuklashda xatolik yuz berdi.")
    await call.answer()

@dp.message(F.text == "💎 Valyuta kurslari")
async def get_currency(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/") as resp:
                data = await resp.json()
                usd = next((i for i in data if i["Ccy"] == "USD"), None)
                eur = next((i for i in data if i["Ccy"] == "EUR"), None)
                rub = next((i for i in data if i["Ccy"] == "RUB"), None)

                text = "📊 **Markaziy Bank rasmiy kurslari:**\n\n"
                if usd: text += f"🇺🇸 1 USD = **{usd['Rate']}** so'm\n"
                if eur: text += f"🇪🇺 1 EUR = **{eur['Rate']}** so'm\n"
                if rub: text += f"🇷🇺 1 RUB = **{rub['Rate']}** so'm\n"
                await message.answer(text, parse_mode="Markdown")
    except Exception:
        await message.answer("Valyutani olishda xatolik bo'ldi.")

@dp.message(F.text == "📝 Shaxsiy Eslatmalar")
async def show_notes(message: types.Message, state: FSMContext):
    cursor.execute("SELECT id, note_text, created_at FROM notes WHERE user_id = ?", (message.from_user.id,))
    notes = cursor.fetchall()
    res = "📝 **Sizning eslatmalaringiz:**\n\n" if notes else "Sizda hali eslatmalar yo'q.\n"
    for n in notes: res += f"📌 **{n[0]}**. {n[1]} _({n[2]})_\n"
    res += "\nYangi eslatma matnini yuboring:"
    await state.set_state(BotStates.waiting_for_note)
    await message.answer(res, parse_mode="Markdown")

@dp.message(BotStates.waiting_for_note)
async def save_note(message: types.Message, state: FSMContext):
    cursor.execute("INSERT INTO notes (user_id, note_text, created_at) VALUES (?, ?, ?)", 
                   (message.from_user.id, message.text, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    await message.answer("✅ Eslatma saqlandi!", reply_markup=main_keyboard())
    await state.clear()

# --- WEB SERVER ---
async def init_app():
    app = web.Application()
    app.router.add_get('/health', lambda r: web.Response(text="Server Online"))
    current_dir = os.path.dirname(os.path.realpath(__file__))
    app.router.add_static('/', path=current_dir, name='static', show_index=True)
    return app

async def main():
    port = int(os.environ.get("PORT", 10000))
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
