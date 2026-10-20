import asyncio
import logging
import os
import json
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web

from sqlalchemy import Column, Integer, String, DateTime, Float, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token va Admin ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = os.getenv("ADMIN_ID", "YOUR_TELEGRAM_ID_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://xudaynazarovdadaxon012-sketch.github.io/telegram-bot//miniapp")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Database (SQLite) sozlamalari
DATABASE_URL = "sqlite+aiosqlite:///smart_booking.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSessionLocal, expire_on_commit=False)
Base = declarative_base()

# 1. Baza jadvallari (Models)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String)
    service_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    booking_time = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Bazani yaratish
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 2. Telegram Bot Handlerlari
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalars().first()
        if not user:
            new_user = User(telegram_id=message.from_user.id, full_name=message.from_user.full_name)
            session.add(new_user)
            await session.commit()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Navbatga yozilish (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        "<b>Smart Booking</b> avtomatlashtirilgan navbatga yozilish tizimiga xush kelibsiz.\n"
        "Quyidagi tugma orqali o'zingizga qulay xizmat va vaqtni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Mini App'dan yuborilgan ma'lumotni qabul qilish
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        service_name = data.get("service")
        price = data.get("price")
        booking_time = data.get("time")

        # Bazaga saqlash
        async with AsyncSessionLocal() as session:
            booking = Booking(
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                service_name=service_name,
                price=float(price),
                booking_time=booking_time
            )
            session.add(booking)
            await session.commit()

        # Mijozga javob
        await message.answer(
            f"✅ <b>Navbatingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
            f"📌 <b>Xizmat:</b> {service_name}\n"
            f"💵 <b>Narxi:</b> {price:,.0f} so'm\n"
            f"🕒 <b>Vaqti:</b> {booking_time}\n\n"
            "Tashrifingizni kutib qolamiz!",
            parse_mode="HTML"
        )

        # Admin/Biznes egasiga xabarnoma yuborish
        if ADMIN_ID and ADMIN_ID != "YOUR_TELEGRAM_ID_HERE":
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>Yangi navbat!</b>\n\n"
                     f"👤 <b>Mijoz:</b> {message.from_user.full_name} (@{message.from_user.username})\n"
                     f"📌 <b>Xizmat:</b> {service_name}\n"
                     f"💵 <b>Narxi:</b> {price:,.0f} so'm\n"
                     f"🕒 <b>Vaqti:</b> {booking_time}",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await message.answer("⚠️ Ma'lumotlarni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

# 3. Aiohttp Web Server (miniapp.html faylini o'qib beradi)
async def handle_miniapp(request):
    try:
        with open("miniapp.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>miniapp.html fayli topilmadi!</h1>", content_type="text/html", status=404)

app = web.Application()
app.router.add_get("/miniapp", handle_miniapp)

# 4. Asosiy ishga tushirish funksiyasi
async def main():
    await init_db()
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logging.info("Web Server va Telegram Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
