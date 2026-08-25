import asyncio
from datetime import datetime
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
import requests

# Bot tokeningizni shu yerga qo'ying
API_TOKEN = "8760162640:AAGhmn9AtwtXIvk234ETV-gKA6aeCQKDPnY"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# --- FSM Holatlari ---
class WeatherState(StatesGroup):
  waiting_for_city = State()


class ReminderState(StatesGroup):
  waiting_for_text = State()
  waiting_for_time = State()


# --- Ma'lumotlar bazasi ---
conn = sqlite3.connect("reminders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    remind_time TEXT
)
""")
conn.commit()


# --- Asosiy Menyudagi Tugmalar ---
def get_main_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="➕ Yangi eslatma qo'shish",
                  callback_data="add_reminder",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📝 Eslatmalarim", callback_data="list_reminders"
              )
          ],
          [
              InlineKeyboardButton(
                  text="💵 Valyuta kursi", callback_data="valyuta"
              ),
              InlineKeyboardButton(text="🌤 Ob-havo", callback_data="obhavo"),
          ],
      ]
  )


# --- /start komandasi ---
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
  await state.clear()
  await message.answer(
      f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
      "Men sizning ko'p funksiyali yordamchingizman. Quyidagi bo'limlardan birini tanlang:",
      reply_markup=get_main_keyboard(),
  )


# --- 1. VALYUTA KURSLARI ---
@dp.callback_query(F.data == "valyuta")
async def get_currency(callback: types.CallbackQuery):
  try:
    url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    res = requests.get(url).json()

    usd = next(item for item in res if item["Ccy"] == "USD")["Rate"]
    eur = next(item for item in res if item["Ccy"] == "EUR")["Rate"]
    rub = next(item for item in res if item["Ccy"] == "RUB")["Rate"]

    text = (
        f"💵 **Bugungi valyuta kurslari (MB):**\n\n"
        f"🇺🇸 1 USD = {usd} so'm\n"
        f"🇪🇺 1 EUR = {eur} so'm\n"
        f"🇷🇺 1 RUB = {rub} so'm"
    )
    await callback.message.answer(
        text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )
  except Exception:
    await callback.message.answer(
        "Valyuta kurslarini olishda xatolik yuz berdi."
    )
  await callback.answer()


# --- 2. OB-HAVO ---
@dp.callback_query(F.data == "obhavo")
async def ask_city(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(WeatherState.waiting_for_city)
  await callback.message.answer(
      "🌤 Qaysi shaharning ob-havosi kerak?\n\nIltimos, shahar nomini matn sifatida yozib yuboring (masalan: *Samarqand*, *Toshkent*, *Buxoro*):",
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.message(WeatherState.waiting_for_city)
async def weather_by_city(message: types.Message, state: FSMContext):
  city_name = message.text.strip()
  geo_url = (
      f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
  )
  geo_res = requests.get(geo_url).json()

  if geo_res.get("results"):
    lat = geo_res["results"][0]["latitude"]
    lon = geo_res["results"][0]["longitude"]
    found_name = geo_res["results"][0]["name"]

    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather_res = requests.get(weather_url).json()

    temp = weather_res["current_weather"]["temperature"]
    wind = weather_res["current_weather"]["windspeed"]

    text = (
        f"🌤 **{found_name} shahridagi hozirgi ob-havo:**\n\n"
        f"🌡 Harorat: **{temp}°C**\n"
        f"💨 Shamol tezligi: **{wind} km/h**"
    )
    await message.answer(text, parse_mode="Markdown")
  else:
    await message.answer(
        f"❌ '{city_name}' shahri topilmadi. Iltimos, shahar nomini to'g'ri kiriting."
    )

  await message.answer(
      "Boshqa bo'limni tanlashingiz mumkin:", reply_markup=get_main_keyboard()
  )
  await state.clear()


# --- 3. ESLATMALAR ---
@dp.callback_query(F.data == "add_reminder")
async def start_add_reminder(
    callback: types.CallbackQuery, state: FSMContext
):
  await state.set_state(ReminderState.waiting_for_text)
  await callback.message.answer(
      "📝 Nima haqida eslatib qo'yay?\n(Masalan: *Kitob o'qish* yoki *Dori ichish*)"
  )
  await callback.answer()


@dp.message(ReminderState.waiting_for_text)
async def process_reminder_text(message: types.Message, state: FSMContext):
  await state.update_data(reminder_text=message.text)
  await state.set_state(ReminderState.waiting_for_time)
  await message.answer(
      "⏰ Soat nechada eslatay?\nFormat: **SOAT:DAQIQA** (Masalan: `14:30` yoki `09:00`):",
      parse_mode="Markdown",
  )


@dp.message(ReminderState.waiting_for_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
  time_input = message.text.strip()
  try:
    datetime.strptime(time_input, "%H:%M")
    user_data = await state.get_data()
    reminder_text = user_data["reminder_text"]

    cursor.execute(
        "INSERT INTO reminders (user_id, text, remind_time) VALUES (?, ?, ?)",
        (message.from_user.id, reminder_text, time_input),
    )
    conn.commit()

    await message.answer(
        f"✅ Eslatma saqlandi!\n\n📌 **{reminder_text}**\n⏰ Vaqti: **{time_input}**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    await state.clear()
  except ValueError:
    await message.answer(
        "❌ Noto'g'ri vaqt formati! Iltimos, **14:30** shaklida qayta kiriting:"
    )


@dp.callback_query(F.data == "list_reminders")
async def list_reminders(callback: types.CallbackQuery):
  cursor.execute(
      "SELECT text, remind_time FROM reminders WHERE user_id = ?",
      (callback.from_user.id,),
  )
  rows = cursor.fetchall()
  if not rows:
    await callback.message.answer(
        "Sizda hozircha eslatmalar yo'q.", reply_markup=get_main_keyboard()
    )
  else:
    msg = "📝 **Sizning eslatmalaringiz:**\n\n"
    for row in rows:
      msg += f"• {row[0]} — ⏰ _{row[1]}_\n"
    await callback.message.answer(
        msg, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )
  await callback.answer()


# --- FONDAGI ESLATMALARNI TEKSHIRUVCHI ---
async def check_reminders():
  while True:
    try:
      now = datetime.now().strftime("%H:%M")
      cursor.execute(
          "SELECT id, user_id, text FROM reminders WHERE remind_time = ?",
          (now,),
      )
      reminders = cursor.fetchall()

      for rem in reminders:
        rem_id, user_id, text = rem
        await bot.send_message(
            user_id, f"🔔 **ESLATMA!**\n\n📌 {text}", parse_mode="Markdown"
        )
        cursor.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
        conn.commit()
    except Exception as e:
      logging.error(f"Eslatma yuborishda xatolik: {e}")

    await asyncio.sleep(40)


# --- WEB SERVER ---
async def handle(request):
  return web.Response(text="Bot is running online 24/7!")


async def start_web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", 10000)
  await site.start()


# --- ISHGA TUSHIRISH ---
async def main():
  await start_web_server()
  asyncio.create_task(check_reminders())
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
