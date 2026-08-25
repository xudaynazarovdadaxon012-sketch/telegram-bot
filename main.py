import asyncio
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


# Shahar nomini kutish holati (State)
class WeatherState(StatesGroup):
  waiting_for_city = State()


# Ma'lumotlar bazasi
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


# Asosiy menyu
def get_main_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
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


@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
  await state.clear()
  await message.answer(
      f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
      "Men sizning ko'p funksiyali yordamchingizman. "
      "Quyidagi bo'limlardan birini tanlang:",
      reply_markup=get_main_keyboard(),
  )


# --- Valyuta kurslari ---
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


# --- Ob-havo tugmasi bosilganda shahar nomini so'rash ---
@dp.callback_query(F.data == "obhavo")
async def ask_city(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(WeatherState.waiting_for_city)
  await callback.message.answer(
      "🌤 Qaysi shaharning ob-havosi kerak?\n\n"
      "Iltimos, shahar nomini matn sifatida yozib yuboring (masalan: *Samarqand*, *Toshkent*, *Buxoro*, *Namangan*):",
      parse_mode="Markdown",
  )
  await callback.answer()


# --- Foydalanuvchi kiritgan shahar bo'yicha ob-havoni izlash ---
@dp.message(WeatherState.waiting_for_city)
async def weather_by_city(message: types.Message, state: FSMContext):
  city_name = message.text.strip()

  # Shahar koordinatalarini aniqlash API
  geo_url = (
      f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
  )
  geo_res = requests.get(geo_url).json()

  if geo_res.get("results"):
    lat = geo_res["results"][0]["latitude"]
    lon = geo_res["results"][0]["longitude"]
    found_name = geo_res["results"][0]["name"]

    # Ob-havoni olish API
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
        f"❌ '{city_name}' shahri topilmadi. Iltimos, shahar nomini to'g'ri kiritganingizni tekshirib, qayta urinib ko'ring."
    )

  await message.answer(
      "Boshqa bo'limni tanlashingiz mumkin:", reply_markup=get_main_keyboard()
  )
  await state.clear()


# --- Eslatmalarni ko'rish ---
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
      msg += f"• {row[0]} — _{row[1]}_\n"
    await callback.message.answer(
        msg, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )
  await callback.answer()


# Web-server
async def handle(request):
  return web.Response(text="Bot is running online 24/7!")


async def start_web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", 10000)
  await site.start()


async def main():
  await start_web_server()
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
