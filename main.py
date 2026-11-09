import os
import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokeningizni shu yerga yozing
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Ma'lumotlar bazasini yaratish va boshlang'ich savollarni qo'shish
def init_db():
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_1 TEXT NOT NULL,
            option_2 TEXT NOT NULL,
            option_3 TEXT NOT NULL,
            option_4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        sample_questions = [
            ("Python'da funksiya qaysi kalit so'z yordamida e'lon qilinadi?", "function", "def", "fun", "define", 2),
            ("HTML'da sarlavha (heading) uchun eng katta teg qaysi?", "<h6>", "<head>", "<h1>", "<header>", 3),
            ("Python ma'lumotlar turiga qaysi biri kirmaydi?", "int", "float", "real", "str", 3),
            ("Veb-sahifaning tuzilmasini yaratish uchun qaysi til ishlatiladi?", "Python", "CSS", "HTML", "SQL", 3)
        ]
        cursor.executemany("""
            INSERT INTO questions (question, option_1, option_2, option_3, option_4, correct_option)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_questions)
        conn.commit()
    conn.close()

# Test yechish jarayoni uchun FSM holati
class QuizState(StatesGroup):
    taking_test = State()

def get_questions():
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, option_1, option_2, option_3, option_4, correct_option FROM questions")
    rows = cursor.fetchall()
    conn.close()
    return rows

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Dasturlash testini boshlash", callback_data="start_quiz")]
    ])
    await message.answer(
        "Salom! 👋\nJunior dasturchilar uchun intervyu va bilim sinov botiga xush kelibsiz.\n\n"
        "Bilimingizni sinab ko'rish uchun quyidagi tugmani bosing:", 
        reply_markup=keyboard
    )

@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    questions = get_questions()
    if not questions:
        await callback.message.answer("Hozircha testlar mavjud emas.")
        await callback.answer()
        return

    await state.update_data(questions=questions, index=0, score=0)
    await state.set_state(QuizState.taking_test)
    
    await show_question(callback.message, state)
    await callback.answer()

async def show_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]

    if index >= len(questions):
        score = data["score"]
        await message.answer(
            f"🎉 **Test yakunlandi!**\n\n"
            f"Sizning natijangiz: **{score} / {len(questions)}**\n"
            f"Qayta boshlash uchun /start buyrug'ini bosing."
        )
        await state.clear()
        return

    q = questions[index]
    q_id, q_text, opt1, opt2, opt3, opt4, correct = q

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt1, callback_data="ans_1")],
        [InlineKeyboardButton(text=opt2, callback_data="ans_2")],
        [InlineKeyboardButton(text=opt3, callback_data="ans_3")],
        [InlineKeyboardButton(text=opt4, callback_data="ans_4")],
    ])

    await message.answer(f"<b>{index + 1}-savol:</b>\n{q_text}", reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(QuizState.taking_test, F.data.startswith("ans_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    selected_option = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    questions = data["questions"]
    index = data["index"]
    score = data["score"]

    correct_option = questions[index][6]

    if selected_option == correct_option:
        score += 1

    await state.update_data(index=index + 1, score=score)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await show_question(callback.message, state)
    await callback.answer()

async def main():
    init_db()
    dp.include_router(router)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
