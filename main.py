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

# WebApp so'rovlariga CORS ruxsati
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vaqtinchalik Ma'lumotlar Bazasi
db = {
    "users": {},         # {user_id: {"coins": 100, "username": "name"}}
    "promos": {          # Promo-kodlar ro'yxati
        "CYBER2026": 500,
        "WELCOME": 1000
    },
    "used_promos": {},   # {user_id: ["CYBER2026"]}
    "daily_claims": {},  # {user_id: "YYYY-MM-DD"} -> Kuniga 1 marta cheklov
    "withdraws": []      # Yechib olish so'rovlari
}

# ==========================================
# PYDANTIC MODELLARI (Data Schemas)
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

class WithdrawModel(BaseModel):
    user_id: int
    amount: int
    method: str

# ==========================================
# TELEGRAM BOT BUYRUQLARI
# ==========================================
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
    await message.answer("👋 Xush kelibsiz! Mini App-ni ochish uchun tugmani bosing:", reply_markup=kb)

# ==========================================
# API ENDPOINTLARI (MINI APP UCHUN)
# ==========================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Cyber Pro Hub Backend Server Ishlamoqda!"}

# 1. Foydalanuvchi ma'lumotlarini olish
@app.get("/api/get_user")
async def get_user(user_id: int):
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}
    return {"success": True, "coins": db["users"][user_id]["coins"]}

# 2. Kunlik bonus (Kuniga 1 marta cheklov bilan)
@app.post("/api/claim_daily")
async def claim_daily(data: CoinUpdateModel):
    user_id = data.user_id
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Sanani tekshirish
    last_claimed = db["daily_claims"].get(user_id)
    if last_claimed == today_str:
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

# 3. Promo-kod ishlatish
@app.post("/api/use_promo")
async def use_promo(data: PromoModel):
    code = data.code.upper().strip()
    user_id = data.user_id

    if code not in db["promos"]:
        return {"success": False, "message": "Bunday promo-kod mavjud emas!"}

    used_list = db["used_promos"].get(user_id, [])
    if code in used_list:
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

# 4. Fikr va takliflarni Adminga Telegram orqali yuborish
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

# 5. Tap-to-Earn (Tap qilish)
@app.post("/api/tap")
async def tap_coin(data: CoinUpdateModel):
    user_id = data.user_id
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User"}
    
    db["users"][user_id]["coins"] += data.amount
    return {"success": True, "new_balance": db["users"][user_id]["coins"]}

# 6. Yechib olish so'rovi
@app.post("/api/withdraw")
async def request_withdraw(data: WithdrawModel):
    user_id = data.user_id
    if user_id not in db["users"] or db["users"][user_id]["coins"] < data.amount:
        return {"success": False, "message": "Balansingizda yetarli coin yo'q!"}

    db["users"][user_id]["coins"] -= data.amount
    db["withdraws"].append({"user_id": user_id, "amount": data.amount, "method": data.method, "status": "pending"})

    # Adminga xabar yuborish
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💳 **Yangi pul yechish so'rovi!**\n\nUser ID: `{user_id}`\nMiqdor: {data.amount} Coin\nUsul: {data.method}"
        )
    except:
        pass

    return {"success": True, "message": "Yechib olish so'rovi adminga yuborildi!", "new_balance": db["users"][user_id]["coins"]}

# 7. Admin Panel: Statistika va Balans boshqaruvi
@app.get("/api/admin/stats")
async def get_admin_stats(x_user_id: int = Header(...)):
    if x_user_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan!")

    total_coins = sum(u["coins"] for u in db["users"].values())
    return {
        "success": True,
        "total_users": len(db["users"]),
        "total_coins": total_coins,
        "withdraws": db["withdraws"]
    }

@app.post("/api/admin/update_coins")
async def admin_update_coins(data: CoinUpdateModel, x_user_id: int = Header(...)):
    if x_user_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan!")

    if data.user_id not in db["users"]:
        db["users"][data.user_id] = {"coins": 0, "username": "User"}

    db["users"][data.user_id]["coins"] += data.amount
    return {"success": True, "new_balance": db["users"][data.user_id]["coins"]}

# ==========================================
# ASOSIY ISHGA TUSHIRISH (Uvicorn + Bot Polling)
# ==========================================
async def main():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    # FastAPI Server va Telegram Bot pollingni birgalikda yurgizish
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
