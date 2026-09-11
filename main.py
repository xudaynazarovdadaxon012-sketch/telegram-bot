import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

# ==========================================================
# RENDER ENVIRONMENT VARIABLES
# ==========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: 'BOT_TOKEN' muhit o'zgaruvchisi topilmadi!")

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

# Real In-Memory Ma'lumotlar Bazasi
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

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "User"
    
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": username, "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    else:
        db["users"][user_id]["username"] = username

    kb_buttons = []
    if WEBAPP_URL:
        kb_buttons.append([InlineKeyboardButton(text="🚀 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons) if kb_buttons else None
    await message.answer("👋 Xush kelibsiz! Mini App-ni ochish uchun pastdagi tugmani bosing:", reply_markup=kb)

# ----------------- ADMIN API -----------------
@app.get("/api/admin/stats")
async def get_admin_stats(user_id: int):
    # Faqat belgilangan Admin kirishi mumkin
    is_admin = (user_id == ADMIN_ID) or (ADMIN_ID == 0)
    
    total_users = len(db["users"])
    total_coins = sum(u["coins"] for u in db["users"].values())
    pending_withdraws = len([w for w in db["withdraws"] if w.get("status") == "pending"])
    
    user_list = []
    for uid, udata in db["users"].items():
        user_list.append({
            "user_id": uid,
            "username": udata.get("username", "User"),
            "coins": udata.get("coins", 0),
            "joined_at": udata.get("joined_at", "Noma'lum")
        })

    return {
        "success": True,
        "is_admin": is_admin,
        "stats": {
            "total_users": total_users,
            "total_coins": total_coins,
            "pending_withdraws": pending_withdraws,
            "admin_id": ADMIN_ID
        },
        "users": user_list,
        "withdraws": db["withdraws"]
    }

# ----------------- USER API -----------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend server xavfsiz rejimda ishlamoqda!"}

@app.get("/api/get_user")
async def get_user(user_id: int):
    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User", "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return {
        "success": True, 
        "coins": db["users"][user_id]["coins"],
        "is_admin": (user_id == ADMIN_ID)
    }

@app.post("/api/claim_daily")
async def claim_daily(data: CoinUpdateModel):
    user_id = data.user_id
    today_str = datetime.now().strftime("%Y-%m-%d")

    if db["daily_claims"].get(user_id) == today_str:
        return {"success": False, "message": "Kunlik bonusni bugun olib bo'lgansiz! Ertaga qayta urinib ko'ring."}

    if user_id not in db["users"]:
        db["users"][user_id] = {"coins": 0, "username": "User", "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M")}

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
        db["users"][user_id] = {"coins": 0, "username": "User", "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M")}

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
    if ADMIN_ID == 0:
        return {"success": False, "message": "Admin ID sozlanmagan!"}

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
        db["users"][user_id] = {"coins": 0, "username": "User", "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    db["users"][user_id]["coins"] += data.amount
    return {"success": True, "new_balance": db["users"][user_id]["coins"]}

@app.post("/api/withdraw")
async def request_withdraw(data: WithdrawModel):
    user_id = data.user_id
    if user_id not in db["users"] or db["users"][user_id]["coins"] < data.amount:
        return {"success": False, "message": "Balansingizda yetarli coin yo'q!"}

    db["users"][user_id]["coins"] -= data.amount
    db["withdraws"].append({
        "user_id": user_id, 
        "username": db["users"][user_id].get("username", "User"),
        "amount": data.amount, 
        "method": data.method, 
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    if ADMIN_ID != 0:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💳 **Yangi pul yechish so'rovi!**\n\nUser ID: `{user_id}`\nMiqdor: {data.amount} Coin\nUsul: {data.method}"
            )
        except:
            pass

    return {"success": True, "message": "Yechib olish so'rovi adminga yuborildi!", "new_balance": db["users"][user_id]["coins"]}

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
