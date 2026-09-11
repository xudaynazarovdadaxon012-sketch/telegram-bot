import os
import asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

# ==========================================
# SOZLAMALAR
# ==========================================

# Render Environment Variables'dan o'qib olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
# str holatda kelgani uchun int() ga o'giramiz
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# WebApp so'rovlariga ruxsat berish
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vaqtinchalik baza
db = {
    "users": {},
    "promos": {"CYBER2026": 500, "WELCOME": 1000},
    "used_promos": {}
}

# ==========================================
# SCHEMAS
# ==========================================
class FeedbackModel(BaseModel):
    user_id: int
    username: str
    text: str

class PromoModel(BaseModel):
    user_id: int
    code: str

class CoinUpdateModel(BaseModel):
    user_id: int
    amount: int

# ==========================================
# TELEGRAM BOT BUYRUQLARI
# ==========================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("Xush kelibsiz! O'yinni boshlash uchun quyidagi tugmani bosing:", reply_markup=kb)

# ==========================================
# API ENDPOINTLARI (MINI APP UCHUN)
# ==========================================
@app.get("/")
async def root():
    return {"status": "ok", "message": "Server ishlamoqda!"}

@app.get("/api/get_user")
async def get_user(user_id: int):
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}
    return {"success": True, "coins": db["users"][user_id]["coins"]}

@app.post("/api/send_feedback")
async def send_feedback(data: FeedbackModel):
    msg_text = (
        f"📩 **Yangi Fikr / Taklif!**\n\n"
        f"👤 **Kimdan:** @{data.username} (ID: `{data.user_id}`)\n"
        f"💬 **Xabar:**\n{data.text}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=msg_text, parse_mode="Markdown")
        return {"success": True, "message": "Xabar adminga yuborildi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/use_promo")
async def use_promo(data: PromoModel):
    code = data.code.upper().strip()
    user_id = data.user_id

    if code not in db["promos"]:
        return {"success": False, "message": "Bunday promo-kod mavjud emas!"}

    used_list = db["used_promos"].get(user_id, [])
    if code in used_list:
        return {"success": False, "message": "Siz bu promo-kodni ishlatgansiz!"}

    reward = db["promos"][code]
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}

    db["users"][user_id]["coins"] += reward

    if user_id not in db["used_promos"]:
        db["used_promos"][user_id] = []
    db["used_promos"][user_id].append(code)

    return {"success": True, "reward": reward, "new_balance": db["users"][user_id]["coins"]}

@app.post("/api/admin/update_coins")
async def admin_update_coins(data: CoinUpdateModel, x_user_id: int = Header(...)):
    if x_user_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan!")

    if data.user_id not in db["users"]:
        db["users"][data.user_id] = {"coins": 0, "username": "User"}

    db["users"][data.user_id]["coins"] += data.amount
    return {"success": True, "new_balance": db["users"][data.user_id]["coins"]}

# ==========================================
# ASOSIY ISHGA TUSHIRISH (MAIN FUNKSIYASI)
# ==========================================
async def main():
    # Render beradigan PORT-ni olish
    port = int(os.environ.get("PORT", 8000))
    
    # Uvicorn serverini fonda yurgizish
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    # Bot va FastAPI-ni bir vaqtda parallel ishga tushirish
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
