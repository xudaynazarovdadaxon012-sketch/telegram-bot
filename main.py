import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: 'BOT_TOKEN' topilmadi!")

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
    "completed_tasks": {},
    "referrals": {}
}

TASKS = [
    {"id": "tg_channel", "title": "📢 Rasmiy kanalga a'zo bo'lish", "reward": 1000},
    {"id": "invite_3", "title": "👥 3 ta do'stni taklif qilish", "reward": 2000},
    {"id": "tap_100", "title": "⚡️ 100 marta tap bosish", "reward": 500}
]

class PromoModel(BaseModel):
    user_id: int
    code: str

class CoinUpdateModel(BaseModel):
    user_id: int
    amount: int

class TaskCheckModel(BaseModel):
    user_id: int
    task_id: str

class WalletConnectModel(BaseModel):
    user_id: int
    wallet_address: str

class DirectMsgModel(BaseModel):
    admin_id: int
    target_user_id: int
    message: str

class BroadcastMsgModel(BaseModel):
    admin_id: int
    message: str

class BuyBoostModel(BaseModel):
    user_id: int
    boost_type: str

def init_user_if_not_exists(user_id: int, username: str = "User"):
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "coins": 0,
            "username": username,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "taps_count": 0,
            "energy": 1000,
            "max_energy": 1000,
            "last_energy_update": datetime.now().timestamp(),
            "tap_level": 1,
            "wallet": ""
        }

def update_user_energy(user_id: int):
    u = db["users"][user_id]
    now = datetime.now().timestamp()
    passed_sec = int(now - u.get("last_energy_update", now))
    if passed_sec > 0:
        added_energy = passed_sec * 2  # Har sekundda 2 energiya tiklanadi
        u["energy"] = min(u.get("max_energy", 1000), u.get("energy", 1000) + added_energy)
        u["last_energy_update"] = now

@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "User"
    referrer_id = int(command.args) if command.args and command.args.isdigit() else None

    is_new = user_id not in db["users"]
    init_user_if_not_exists(user_id, username)

    if is_new and referrer_id and referrer_id in db["users"] and referrer_id != user_id:
        if referrer_id not in db["referrals"]:
            db["referrals"][referrer_id] = []
        if user_id not in db["referrals"][referrer_id]:
            db["referrals"][referrer_id].append(user_id)
            db["users"][referrer_id]["coins"] += 500
            try:
                await bot.send_message(chat_id=referrer_id, text=f"🎉 @{username} taklifingiz bo'yicha qo'shildi! Sizga **+500 Coin** berildi.")
            except:
                pass

    kb_buttons = []
    if WEBAPP_URL:
        kb_buttons.append([InlineKeyboardButton(text="🚀 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons) if kb_buttons else None
    await message.answer("👋 Xush kelibsiz! Mini App-ni ochish uchun pastdagi tugmani bosing:", reply_markup=kb)

# ----------------- ADMIN API -----------------
@app.get("/api/admin/stats")
async def get_admin_stats(user_id: int):
    is_admin = (user_id == ADMIN_ID) or (ADMIN_ID == 0)
    
    user_list = []
    for uid, udata in db["users"].items():
        user_list.append({
            "user_id": uid,
            "username": udata.get("username", "User"),
            "coins": udata.get("coins", 0),
            "joined_at": udata.get("joined_at", "Noma'lum"),
            "wallet": udata.get("wallet", "")
        })

    return {
        "success": True,
        "is_admin": is_admin,
        "stats": {
            "total_users": len(db["users"]),
            "total_coins": sum(u["coins"] for u in db["users"].values()),
            "total_refs": sum(len(refs) for refs in db["referrals"].values()),
            "admin_id": ADMIN_ID
        },
        "users": user_list
    }

@app.post("/api/admin/send_direct")
async def admin_send_direct(data: DirectMsgModel):
    if ADMIN_ID != 0 and data.admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat berilmadi!"}
    try:
        await bot.send_message(chat_id=data.target_user_id, text=f"💬 **Admin xabari:**\n\n{data.message}")
        return {"success": True, "message": "Xabar muvaffaqiyatli yetkazildi!"}
    except Exception as e:
        return {"success": False, "message": f"Xatolik: {str(e)}"}

@app.post("/api/admin/broadcast")
async def admin_broadcast(data: BroadcastMsgModel):
    if ADMIN_ID != 0 and data.admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat berilmadi!"}
    
    count = 0
    for uid in list(db["users"].keys()):
        try:
            await bot.send_message(chat_id=uid, text=f"📢 **E'lon:**\n\n{data.message}")
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    return {"success": True, "message": f"{count} ta foydalanuvchiga yuborildi!"}

# ----------------- USER API -----------------
@app.get("/api/get_user")
async def get_user(user_id: int):
    init_user_if_not_exists(user_id)
    update_user_energy(user_id)

    u = db["users"][user_id]
    refs_count = len(db["referrals"].get(user_id, []))
    bot_info = await bot.get_me()

    return {
        "success": True,
        "coins": u["coins"],
        "energy": u["energy"],
        "max_energy": u["max_energy"],
        "tap_level": u["tap_level"],
        "wallet": u.get("wallet", ""),
        "is_admin": (user_id == ADMIN_ID or ADMIN_ID == 0),
        "ref_count": refs_count,
        "ref_link": f"https://t.me/{bot_info.username}?start={user_id}",
        "completed_tasks": db["completed_tasks"].get(user_id, []),
        "tasks": TASKS
    }

@app.post("/api/tap")
async def tap_coin(data: CoinUpdateModel):
    user_id = data.user_id
    init_user_if_not_exists(user_id)
    update_user_energy(user_id)

    u = db["users"][user_id]
    tap_power = u.get("tap_level", 1)

    if u["energy"] < tap_power:
        return {"success": False, "message": "Energiya yetarli emas!", "energy": u["energy"], "coins": u["coins"]}

    u["coins"] += tap_power
    u["energy"] -= tap_power
    u["taps_count"] = u.get("taps_count", 0) + 1

    return {"success": True, "new_balance": u["coins"], "energy": u["energy"]}

@app.post("/api/buy_boost")
async def buy_boost(data: BuyBoostModel):
    user_id = data.user_id
    init_user_if_not_exists(user_id)
    u = db["users"][user_id]

    if data.boost_type == "multitap":
        cost = u.get("tap_level", 1) * 1000
        if u["coins"] < cost:
            return {"success": False, "message": f"Tangalar yetarli emas! Narxi: {cost} Coin"}
        u["coins"] -= cost
        u["tap_level"] = u.get("tap_level", 1) + 1
        return {"success": True, "message": f"🚀 Multitap LVL {u['tap_level']} oshirildi!", "new_balance": u["coins"]}

    elif data.boost_type == "max_energy":
        cost = (u.get("max_energy", 1000) // 500) * 1500
        if u["coins"] < cost:
            return {"success": False, "message": f"Tangalar yetarli emas! Narxi: {cost} Coin"}
        u["coins"] -= cost
        u["max_energy"] = u.get("max_energy", 1000) + 500
        return {"success": True, "message": f"⚡️ Maks. energiya {u['max_energy']} ga oshirildi!", "new_balance": u["coins"]}

    return {"success": False, "message": "Noma'lum boost"}

@app.post("/api/connect_wallet")
async def connect_wallet(data: WalletConnectModel):
    init_user_if_not_exists(data.user_id)
    db["users"][data.user_id]["wallet"] = data.wallet_address
    return {"success": True, "message": "💎 TON Hamyon muvaffaqiyatli ulandi!"}

@app.get("/api/leaderboard")
async def get_leaderboard():
    sorted_users = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    top_list = [{"rank": r, "username": u[1].get("username", "User"), "coins": u[1].get("coins", 0)} for r, u in enumerate(sorted_users, start=1)]
    return {"success": True, "leaderboard": top_list}

@app.post("/api/claim_daily")
async def claim_daily(data: CoinUpdateModel):
    user_id = data.user_id
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    user_claim = db["daily_claims"].get(user_id, {"last_date": "", "streak": 0})

    if user_claim.get("last_date") == today_str:
        return {"success": False, "message": "Bugun bonusni olgansiz!"}

    streak = 1
    if user_claim.get("last_date"):
        last_date = datetime.strptime(user_claim["last_date"], "%Y-%m-%d").date()
        if datetime.now().date() - last_date == timedelta(days=1):
            streak = min(user_claim.get("streak", 0) + 1, 5)

    reward = streak * 200
    init_user_if_not_exists(user_id)
    db["users"][user_id]["coins"] += reward
    db["daily_claims"][user_id] = {"last_date": today_str, "streak": streak}

    return {"success": True, "message": f"🎉 {streak}-kunlik bonus: +{reward} Coin!", "new_balance": db["users"][user_id]["coins"]}

@app.post("/api/complete_task")
async def complete_task(data: TaskCheckModel):
    user_id = data.user_id
    task_id = data.task_id

    if user_id not in db["completed_tasks"]:
        db["completed_tasks"][user_id] = []

    if task_id in db["completed_tasks"][user_id]:
        return {"success": False, "message": "Bajarib bo'lingan!"}

    target_task = next((t for t in TASKS if t["id"] == task_id), None)
    if not target_task:
        return {"success": False, "message": "Topilmadi!"}

    db["completed_tasks"][user_id].append(task_id)
    init_user_if_not_exists(user_id)
    db["users"][user_id]["coins"] += target_task["reward"]

    return {"success": True, "message": f"✅ +{target_task['reward']} Coin!", "new_balance": db["users"][user_id]["coins"]}

@app.post("/api/use_promo")
async def use_promo(data: PromoModel):
    code = data.code.upper().strip()
    user_id = data.user_id

    if code not in db["promos"]:
        return {"success": False, "message": "Kod mavjud emas!"}

    if code in db["used_promos"].get(user_id, []):
        return {"success": False, "message": "Kod ishlatilgan!"}

    reward = db["promos"][code]
    init_user_if_not_exists(user_id)
    db["users"][user_id]["coins"] += reward

    if user_id not in db["used_promos"]:
        db["used_promos"][user_id] = []
    db["used_promos"][user_id].append(code)

    return {"success": True, "message": f"🎁 +{reward} Coin!", "new_balance": db["users"][user_id]["coins"]}

async def main():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(server.serve(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
