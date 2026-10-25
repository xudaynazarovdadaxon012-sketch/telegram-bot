import os
import asyncio
import datetime
import logging
from enum import Enum as PyEnum

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# -------------------------------------------------------------------
# 1. SOZLAMALAR (RENDER ENVIRONMENT VARIABLES DAN O'QISH)
# -------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@my_marketplace_channel")
DATABASE_URL = "sqlite+aiosqlite:///marketplace.db"

logging.basicConfig(level=logging.INFO)

# (Qolgan kodlar o'zgarishsiz ishlayveradi...)

# -------------------------------------------------------------------
# 2. SQLALCHEMY MODELLARI VA BAZA SOZLAMASI
# -------------------------------------------------------------------
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ItemStatus(str, PyEnum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    game: Mapped[str] = mapped_column(String(64))  # Roblox, CS, Valorant va h.k.
    level_range: Mapped[str] = mapped_column(String(32))  # "1-20 lvl", "50+ lvl"
    features: Mapped[str] = mapped_column(Text)  # "Rare skinlar | Donat qilingan"
    credentials: Mapped[str] = mapped_column(Text)  # Login:pass xaridorga beriladi

    suggested_price: Mapped[float] = mapped_column(Float)  # Bot tavsiya qilgan narx
    final_price: Mapped[float] = mapped_column(Float)  # Sotuvchi tasdiqlagan narx

    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus), default=ItemStatus.ACTIVE
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    total_amount: Mapped[float] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float)  # 1% komissiya
    seller_amount: Mapped[float] = mapped_column(Float)  # 99% sotuvchiga

    is_completed: Mapped[bool] = mapped_column(default=False)
    escrow_expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime
    )  # 1 soatlik taymer


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------------------------------------------------------------
# 3. FSM (STATE) VA ALGORITM
# -------------------------------------------------------------------
class SellFlow(StatesGroup):
    select_game = State()
    select_level = State()
    select_features = State()
    input_credentials = State()
    confirm_price = State()
    edit_price = State()


def calculate_price(game: str, level: str, features: list[str]) -> float:
    """Botning avtomatik va adolatli narxlash algoritmi"""
    base_price = 15000.0 if game == "Roblox" else 25000.0

    # Level qo'shimchasi
    if level == "21-50 lvl":
        base_price += 15000.0
    elif level == "50+ lvl":
        base_price += 35000.0

    # Feature qo'shimchasi
    if "Rare Skinlar" in features:
        base_price += 20000.0
    if "Donat qilingan" in features:
        base_price += 15000.0
    if "Pochtasi toza" in features:
        base_price += 10000.0

    return base_price


# -------------------------------------------------------------------
# 4. BOT HANDLERLARI (INLINE INTERFEYS)
# -------------------------------------------------------------------
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 Akkaunt Sotish (E'lon berish)", callback_data="sell_account"
                )
            ]
        ]
    )
    await message.answer(
        f"Salom, {message.from_user.full_name}!\n"
        f"Marketplace botimizga xush kelibsiz. Akkaunt sotish uchun quyidagi tugmani bosing:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "sell_account")
async def start_sell(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧱 Roblox", callback_data="game_Roblox"),
                InlineKeyboardButton(text="🎯 CS:GO / Steam", callback_data="game_CS"),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Valorant", callback_data="game_Valorant"
                ),
                InlineKeyboardButton(
                    text="🧊 Minecraft", callback_data="game_Minecraft"
                ),
            ],
        ]
    )
    await call.message.edit_text("1️⃣ O'yin turini tanlang:", reply_markup=kb)
    await state.set_state(SellFlow.select_game)


@router.callback_query(SellFlow.select_game, F.data.startswith("game_"))
async def process_game(call: CallbackQuery, state: FSMContext):
    game = call.data.split("_")[1]
    await state.update_data(game=game)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 - 20 lvl", callback_data="lvl_1-20 lvl"),
                InlineKeyboardButton(
                    text="21 - 50 lvl", callback_data="lvl_21-50 lvl"
                ),
            ],
            [
                InlineKeyboardButton(text="50+ lvl", callback_data="lvl_50+ lvl"),
            ],
        ]
    )
    await call.message.edit_text(
        f"🎮 O'yin: **{game}**\n2️⃣ Akkaunt darajasini (Level) tanlang:",
        reply_markup=kb,
    )
    await state.set_state(SellFlow.select_level)


@router.callback_query(SellFlow.select_level, F.data.startswith("lvl_"))
async def process_level(call: CallbackQuery, state: FSMContext):
    level = call.data.split("_")[1]
    await state.update_data(level=level, selected_features=[])

    await show_features_keyboard(call.message, state)
    await state.set_state(SellFlow.select_features)


async def show_features_keyboard(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_features", [])

    def mark(feat):
        return "✅ " if feat in selected else ""

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{mark('Rare Skinlar')}Rare Skinlar",
                    callback_data="feat_Rare Skinlar",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{mark('Donat qilingan')}Donat qilingan",
                    callback_data="feat_Donat qilingan",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{mark('Pochtasi toza')}Pochtasi toza",
                    callback_data="feat_Pochtasi toza",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Davom etish", callback_data="feat_done"
                )
            ],
        ]
    )
    await message.edit_text(
        "3️⃣ Akkaunt xususiyatlarini belgilang (bir nechta tanlash mumkin):",
        reply_markup=kb,
    )


@router.callback_query(SellFlow.select_features, F.data.startswith("feat_"))
async def process_features(call: CallbackQuery, state: FSMContext):
    feat = call.data.replace("feat_", "")
    data = await state.get_data()
    selected = data.get("selected_features", [])

    if feat == "done":
        await call.message.edit_text(
            "4️⃣ Akkaunt login va parolini yozib yuboring:\n"
            "*(Bu ma'lumot faqat xaridor to'lov qilgach avtomatik beriladi)*"
        )
        await state.set_state(SellFlow.input_credentials)
        return

    if feat in selected:
        selected.remove(feat)
    else:
        selected.append(feat)

    await state.update_data(selected_features=selected)
    await show_features_keyboard(call.message, state)


@router.message(SellFlow.input_credentials)
async def process_credentials(message: Message, state: FSMContext):
    credentials = message.text
    data = await state.get_data()

    game = data["game"]
    level = data["level"]
    features = data["selected_features"]

    # Avtomatik narx hisoblash
    suggested_price = calculate_price(game, level, features)
    await state.update_data(
        credentials=credentials,
        suggested_price=suggested_price,
        final_price=suggested_price,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Shu narxda tasdiqlash", callback_data="confirm_price"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Narxni o'zgartirish", callback_data="edit_price"
                )
            ],
        ]
    )

    feats_str = " | ".join(features) if features else "Yo'q"
    await message.answer(
        f"📊 **E'lon Tayyor!**\n\n"
        f"🎮 O'yin: {game}\n"
        f"📈 Level: {level}\n"
        f"⭐ Xususiyatlar: {feats_str}\n\n"
        f"🤖 **Bot tomonidan tavsiya etilgan narx:** {suggested_price:,.0f} so'm\n\n"
        f"Ushbu narxga rozimisiz yoki o'zingiz o'zgartirasizmi?",
        reply_markup=kb,
    )
    await state.set_state(SellFlow.confirm_price)


@router.callback_query(SellFlow.confirm_price, F.data == "edit_price")
async def ask_new_price(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "✏️ O'zingiz xohlagan narxni raqam bilan kiriting (masalan: 60000):"
    )
    await state.set_state(SellFlow.edit_price)


@router.message(SellFlow.edit_price)
async def set_custom_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, narxni faqat raqamlarda kiriting!")
        return

    new_price = float(message.text)
    await state.update_data(final_price=new_price)

    data = await state.get_data()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Kanalga E'lon Qilish", callback_data="publish_item"
                )
            ]
        ]
    )
    await message.answer(
        f"✅ Narx yangilandi: **{new_price:,.0f} so'm**\n"
        f"E'lonni e'lon qilishga tayyormisiz?",
        reply_markup=kb,
    )
    await state.set_state(SellFlow.confirm_price)


@router.callback_query(SellFlow.confirm_price, F.data.in_(["confirm_price", "publish_item"]))
async def publish_item(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    async with async_session() as session:
        # Userni bazadan topamiz/yaratamiz
        db_user = await session.get(User, call.from_user.id)
        if not db_user:
            db_user = User(
                id=call.from_user.id,
                telegram_id=call.from_user.id,
                full_name=call.from_user.full_name,
                username=call.from_user.username,
            )
            session.add(db_user)
            await session.commit()

        # Item hosil qilish
        feats_str = " | ".join(data["selected_features"]) if data["selected_features"] else "Standart"
        new_item = Item(
            seller_id=db_user.id,
            game=data["game"],
            level_range=data["level"],
            features=feats_str,
            credentials=data["credentials"],
            suggested_price=data["suggested_price"],
            final_price=data["final_price"],
        )
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)

        item_id = new_item.id

    await state.clear()
    await call.message.edit_text("🎉 Akkauntingiz muvaffaqiyatli e'longa joylandi!")

    # Kanalga post berish
    post_text = (
        f"📦 **YANGI AKKAUNT SOTUVDA!** #{data['game']}\n\n"
        f"🎮 **O'yin:** {data['game']}\n"
        f"📊 **Daraja:** {data['level']}\n"
        f"⭐ **Xususiyatlar:** {feats_str}\n"
        f"💰 **Narxi:** {data['final_price']:,.0f} so'm\n\n"
        f"🛡 *Xarid 1 soatlik Escrow (kafolat) bilan amalga oshiriladi.*"
    )

    kb_buy = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Sotib olish",
                    url=f"https://t.me/{(await bot.get_me()).username}?start=buy_{item_id}",
                )
            ]
        ]
    )

    try:
        await bot.send_message(CHANNEL_ID, post_text, reply_markup=kb_buy)
    except Exception as e:
        logging.error(f"Kanalga post joylashda xato: {e}")


# -------------------------------------------------------------------
# 5. ASOSIY ISHGA TUSHIRISH (MAIN)
# -------------------------------------------------------------------
async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
