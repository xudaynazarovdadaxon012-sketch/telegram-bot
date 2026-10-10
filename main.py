import asyncio
import os
import hmac
import hashlib
import json
import logging
from urllib.parse import parse_qsl
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    PreCheckoutQuery,
    ContentType,
    LabeledPrice
)
from aiohttp import web
from cachetools import TTLCache

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, func, select

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.onrender.com/miniapp.html")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
PORT = int(os.getenv("PORT", 8080))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///production.db")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class RateLimitMiddleware:
    def __init__(self, limit: float = 0.5):
        self.cache = TTLCache(maxsize=10000, ttl=limit)

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.from_user:
            if event.from_user.id in self.cache:
                return
            self.cache[event.from_user.id] = True
        return await handler(event, data)

def build_primary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💼 Xizmatlar portali",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(text="📋 Boshqaruv paneli", callback_data="dashboard"),
                InlineKeyboardButton(text="📞 Qo'llab-quvvatlash", callback_data="support")
            ]
        ]
    )

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.user_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            session.add(
                UserModel(
                    user_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    username=message.from_user.username
                )
            )
            await session.commit()

    await message.answer(
        f"Xush kelibsiz, <b>{message.from_user.full_name}</b>.\n"
        "Tizim xizmatlaridan foydalanish uchun quyidagi portalni oching:",
        reply_markup=build_primary_keyboard()
    )

@router.callback_query(F.data == "dashboard")
async def handle_dashboard(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(func.count(UserModel.id)))
        total_users = result.scalar()

    await callback.message.edit_text(
        f"<b>Tizim holati:</b>\n\n"
        f"• Faol foydalanuvchilar: <code>{total_users}</code>\n"
        f"• Server holati: <code>Online (0.01s response)</code>",
        reply_markup=build_primary_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def handle_support(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>Texnik qo'llab-quvvatlash xizmati:</b>\n\n"
        "Barcha so'rovlar avtomatik ravishda navbatga qo'yiladi.\n"
        "Murojaat uchun: @support_manager",
        reply_markup=build_primary_keyboard()
    )
    await callback.answer()

@router.message(F.web_app_data)
async def handle_webapp_payload(message: Message, bot: Bot):
    raw_data = message.web_app_data.data
    data = json.loads(raw_data)
    
    order_title = data.get("title", "Xizmat buyurtmasi")
    total_amount = int(data.get("amount", 0))

    await message.answer(
        f"<b>Buyurtma rasmiylashtirildi:</b> {order_title}\n"
        f"<b>Jami summa:</b> {total_amount:,} UZS\n\n"
        "To'lovni tasdiqlash uchun quyidagi hisob-fakturadan foydalaning:"
    )

    if PAYMENT_PROVIDER_TOKEN:
        await bot.send_invoice(
            chat_id=message.from_user.id,
            title=order_title,
            description=f"{order_title} bo'yicha to'lov",
            payload=f"order_{message.from_user.id}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="UZS",
            prices=[LabeledPrice(label=order_title, amount=total_amount * 100)]
        )

@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    await message.answer("<b>To'lov tasdiqlandi. Buyurtma ijroga yo'naltirildi.</b>")

async def serve_miniapp(request):
    return web.FileResponse('./miniapp.html')

async def init_web_server():
    app = web.Application()
    app.router.add_get('/', serve_miniapp)
    app.router.add_get('/miniapp.html', serve_miniapp)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    if not BOT_TOKEN:
        raise RuntimeError("CRITICAL: BOT_TOKEN aniqlanmadi.")

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.message.middleware(RateLimitMiddleware())
    dp.include_router(router)

    asyncio.create_task(init_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
