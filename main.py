import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
import requests

# Bot tokeningizni shu yerga qo'ying
API_TOKEN = "8760162640:AAGhmn9AtwtXIvk234ETV-gKA6aeCQKDPnY"

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratish
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Ma'lumotlar bazasi (SQLite) ---
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
async def send_welcome(message: types.Message):
  await message.answer(
      f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
      "Men sizning ko'p funksiyali yordamchingizman. "
      "Quyidagi bo'limlardan birini tanlang:",
      reply_markup=get_main_keyboard(),
  )


# --- Valyuta kurslarini olish ---
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
  except Exception as e:
    await callback.message.answer(
        "Valyuta kurslarini olishda xatolik yuz berdi."
    )
  await callback.answer()


# --- Ob-havo ma'lumotlarini olish ---
@dp.callback_query(F.data == "obhavo")
async def get_weather(callback: types.CallbackQuery):
  try:
    # Toshkent koordinatalari uchun bepul ob-havo API
    url = "https://api.open-meteo.com/v1/forecast?latitude=41.2646&longitude=69.2163&current_weather=true"
    res = requests.get(url).json()
    temp = res["current_weather"]["temperature"]
    wind = res["current_weather"]["windspeed"]

    text = (
        f"🌤 **Toshkent shahridagi hozirgi ob-havo:**\n\n"
        f"🌡 Harorat: **{temp}°C**\n"
        f"💨 Shamol tezligi: **{wind} km/h**"
    )
    await callback.message.answer(
        text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )
  except Exception as e:
    await callback.message.answer("Ob-havoni olishda xatolik yuz berdi.")
  await callback.answer()


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


# --- Web-server (Render uxlab qolmasligi uchun) ---
async def handle(request):
  return web.Response(text="Bot is running online 24/7!")


async def start_web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", 10000)
  await site.start()


# --- Asosiy ishga tushirish funksiyasi ---
async def main():
  await start_web_server()
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
