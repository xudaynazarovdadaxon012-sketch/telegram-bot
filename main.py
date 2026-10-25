import asyncio
import logging
import sys
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Boolean, Float, select

# --- SOZLAMALAR ---
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # O'zingizning Telegram ID raqamingiz
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_marketplace_channel")  # E'lonlar boradigan kanal

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# --- BAZA (SQLALCHEMY) ---
engine = create_async_engine("sqlite+aiosqlite:///marketplace.db", echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)

class Advertisement(Base):
    __tablename__ = "advertisements"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    price: Mapped[float] = mapped_column(Float)
    tier: Mapped[str] = mapped_column(String(32))  # free, cheap, normal, vip
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- FSM (HOLATLAR) ---
class CashSaleState(StatesGroup):
    waiting_for_amount = State()

class FeedbackState(StatesGroup):
    waiting_for_text = State()

router = Router()

# --- ASOSIY MENYU ---
def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Valyuta (Cash) sotish [+1% Yashirin komissiya]", callback_data="sell_cash")],
            [InlineKeyboardButton(text="📢 E'lon berish va Tariflar", callback_data="ads_info")],
            [InlineKeyboardButton(text="✍️ E'tiroz / Taklif yozish", callback_data="leave_feedback")]
        ]
    )

# --- START BUYRUG'I ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            session.add(User(telegram_id=message.from_user.id))
            await session.commit()

    await message.answer(
        "👋 Xush kelibsiz! O'yin akkauntlari va valyutalari savdo botiga marhamat.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard()
    )

# --- 1% YASHIRIN KOMISSIYALI CASH (VALYUTA) SOTISH ---
@router.callback_query(F.data == "sell_cash")
async def sell_cash_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "💵 Sotmoqchi bo'lgan valyurangiz narxini kiriting (Masalan: `100000`):"
    )
    await state.set_state(CashSaleState.waiting_for_amount)
    await callback.answer()

@router.message(CashSaleState.waiting_for_amount)
async def process_cash_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        seller_price = float(message.text)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting! Qaytadan urinib ko'ring:")
        return

    # Yashirin 1% komissiya hisoblash
    commission_rate = 0.01
    final_price = seller_price * (1 + commission_rate)  # Xaridor ko'radigan narx
    admin_commission = final_price - seller_price       # Sizning foydangiz

    # Kanalga chiqarish
    # Bot username'ini oldindan olib qo'yamiz
bot_info = await bot.get_me()
bot_username = bot_info.username

post_text = (
    f"🎮 **O'yin Valyutasi Savdosi!**\n\n"
    f"💰 Narxi: `{final_price:.0f}` so'm\n"
    f"🛡 Kafolat: 1 soatlik Escrow tizimi\n\n"
    f"Sotib olish uchun botga o'ting: @{bot_username}"
)
    
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        await message.answer(
            f"✅ E'loningiz muvaffaqiyatli kanalga joylandi!\n"
            f"Siz belgilagan narx: {seller_price:.0f} so'm\n"
            f"Xaridorga ko'rsatilgan narx: {final_price:.0f} so'm"
        )
    except Exception as e:
        await message.answer(f"❌ Kanalga chiqarishda xatolik: {e}")

    await state.clear()

# --- E'TIROZ / TAKLIF QISMI ---
@router.callback_query(F.data == "leave_feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Taklif, e'tiroz yoki shikoyatingizni yozib yuboring:"
    )
    await state.set_state(FeedbackState.waiting_for_text)
    await callback.answer()

@router.message(FeedbackState.waiting_for_text)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    user = message.from_user
    admin_text = (
        f"📩 **Yangi e'tiroz / taklif!**\n\n"
        f"👤 Kimdan: @{user.username or 'Yo\'q'} (ID: `{user.id}`)\n"
        f"📄 Xabar: {message.text}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
        await message.answer("✅ Xabaringiz adminga yuborildi!")
    except Exception:
        await message.answer("❌ Xabar yuborishda xatolik yuz berdi.")
    await state.clear()

# --- ADMIN REKLAMA BUYRUG'I (/send_ad) ---
@router.message(Command("send_ad"))
async def broadcast_ad(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return

    ad_text = message.text.replace("/send_ad ", "")
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        users = result.scalars().all()

        success_count = 0
        for user_id in users:
            try:
                await bot.send_message(chat_id=user_id, text=ad_text)
                success_count += 1
            except Exception:
                continue

    await message.answer(f"✅ Reklama {success_count} ta foydalanuvchiga yuborildi!")

# --- ISHGA TUSHIRISH ---
async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
