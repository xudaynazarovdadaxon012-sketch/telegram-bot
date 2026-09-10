import os
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://telegram-bot-7n6t.onrender.com")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_PATH = "database.db"

# --- DATABASE INIT ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_text TEXT
            )
        """)
        await db.commit()

async def add_user(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
        await db.commit()

# --- BOT HANDLERS ---
@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await add_user(message.from_user.id, message.from_user.full_name)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Ultra Cyber Hub (10 Modul)",
                    web_app=WebAppInfo(url=f"{RENDER_URL}/miniapp")
                )
            ]
        ]
    )
    await message.answer(
        f"👋 Salom, **{message.from_user.first_name}**!\n\n"
        "**Ultra Cyber Workspace** platformasiga xush kelibsiz.\n"
        "Siz uchun 10 ta unikal neon modulli unumdorlik markazi tayyor bo'ldi. Boshlash uchun tugmani bosing:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- WEB ROUTES ---
async def serve_miniapp(request):
    return web.FileResponse('./templates/miniapp.html')

async def get_tasks(request):
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "tasks": []})
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT task_text FROM tasks WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            tasks = [{"text": r[0]} for r in rows]
    return web.json_response({"ok": True, "tasks": tasks})

async def add_task_api(request):
    data = await request.json()
    user_id = data.get("user_id")
    task_text = data.get("text")
    if user_id and task_text:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO tasks (user_id, task_text) VALUES (?, ?)", (user_id, task_text))
            await db.commit()
        return web.json_response({"ok": True})
    return web.json_response({"ok": False}, status=400)

async def health_check(request):
    return web.Response(text="Bot is Live!")

# --- MAIN RUNNER ---
async def main():
    await init_db()
    
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/miniapp', serve_miniapp)
    app.router.add_get('/api/tasks', get_tasks)
    app.router.add_post('/api/tasks/add', add_task_api)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
