import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

# ==========================================
# SOZLAMALAR (Render Environment Variables)
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-mini-app-url.onrender.com")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vaqtinchalik DB
db = {
    "users": {},
    "promos": {
        "CY83R-9X2Q": 500,
        "W3LC-77KP-99": 1000,
        "B300-X7M2": 300,
        "M3GA-88ZZ-2026": 5000
    },
    "used_promos": {},
    "daily_claims": {},
    "withdraws": []
}

# Modellar
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

class WithdrawModel(BaseModel):
    user_id: int
    amount: int
    method: str

# Bot Buyruqlari
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": message.from_user.username or "User"}

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Cyber Pro Hub Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("👋 Xush kelibsiz! Mini App'ni ochish uchun tugmani bosing:", reply_markup=kb)

# API Endpointlari
@app.get("/")
async def root():
    return {"status": "ok", "message": "Cyber Pro Hub Backend Server Ishlamoqda!"}

@app.get("/api/get_user")
async def get_user(user_id: int):
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}
    return {"success": True, "coins": db["users"][user_id]["coins"]}

@app.post("/api/claim_daily")
async def claim_daily(data: CoinUpdateModel):
    user_id = data.user_id
    today_str = datetime.now().strftime("%Y-%m-%d")

    if db["daily_claims"].get(user_id) == today_str:
        return {"success": False, "message": "Kunlik bonusni bugun olib bo'lgansiz! Ertaga qayta urinib ko'ring."}

    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}

    reward = 200
    db["users"][user_id]["coins"] += reward
    db["daily_claims"][user_id] = today_str

    return {
        "success": True,
        "message": f"🎉 +{reward} Coin olindi!",
        "new_balance": db["users"][user_id]["coins"]
    }

@app.post("/api/use_promo")
async def use_promo(data: PromoModel):
    code = data.code.upper().strip()
    user_id = data.user_id

    if code not in db["promos"]:
        return {"success": False, "message": "Bunday promo-kod mavjud emas!"}

    if code in db["used_promos"].get(user_id, []):
        return {"success": False, "message": "Siz bu promo-kodni ishlatib bo'lgansiz!"}

    reward = db["promos"][code]
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}

    db["users"][user_id]["coins"] += reward

    if user_id not in db["used_promos"]:
        db["used_promos"][user_id] = []
    db["used_promos"][user_id].append(code)

    return {
        "success": True, 
        "reward": reward, 
        "new_balance": db["users"][user_id]["coins"],
        "message": f"🎁 Promo-kod faollashdi! +{reward} Coin"
    }

@app.post("/api/send_feedback")
async def send_feedback(data: FeedbackModel):
    msg_text = (
        f"📩 **Yangi Fikr / Taklif!**\n\n"
        f"👤 **Kimdan:** @{data.username} (ID: `{data.user_id}`)\n"
        f"💬 **Xabar:**\n{data.text}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=msg_text, parse_mode="Markdown")
        return {"success": True, "message": "Xabaringiz adminga yuborildi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot xabar yubora olmadi: {str(e)}")

@app.post("/api/tap")
async def tap_coin(data: CoinUpdateModel):
    user_id = data.user_id
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}
    
    db["users"][user_id]["coins"] += data.amount
    return {"success": True, "new_balance": db["users"][user_id]["coins"]}

@app.post("/api/withdraw")
async def request_withdraw(data: WithdrawModel):
    user_id = data.user_id
    if user_id not in db["users"] or db["users"][user_id]["coins"] < data.amount:
        return {"success": False, "message": "Balansingizda yetarli coin yo'q!"}

    db["users"][user_id]["coins"] -= data.amount
    db["withdraws"].append({"user_id": user_id, "amount": data.amount, "method": data.method, "status": "pending"})

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💳 **Yangi pul yechish so'rovi!**\n\nUser ID: `{user_id}`\nMiqdor: {data.amount} Coin\nUsul: {data.method}"
        )
    except:
        pass

    return {"success": True, "message": "Yechib olish so'rovi adminga yuborildi!", "new_balance": db["users"][user_id]["coins"]}

# Serverni yurgizish
async def main():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
