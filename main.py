import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

from database import load_db, save_db, init_user, update_user_energy

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

TASKS = [
    {"id": "tg_channel", "title": "📢 Rasmiy kanalga a'zo bo'lish", "reward": 1000},
    {"id": "invite_3", "title": "👥 3 ta do'stni taklif qilish", "reward": 2000},
    {"id": "tap_100", "title": "⚡️ 100 marta tap bosish", "reward": 500}
]

class CoinModel(BaseModel):
    user_id: int
    amount: int = 1

class TaskModel(BaseModel):
    user_id: int
    task_id: str

class WalletModel(BaseModel):
    user_id: int
    wallet_address: str

class BoostModel(BaseModel):
    user_id: int
    boost_type: str

class DirectMsgModel(BaseModel):
    admin_id: int
    target_user_id: int
    message: str

class BroadcastMsgModel(BaseModel):
    admin_id: int
    message: str

@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "User"
    referrer_id = command.args if command.args and command.args.isdigit() else None

    db = load_db()
    is_new = str(user_id) not in db["users"]
    init_user(user_id, username)

    if is_new and referrer_id and referrer_id in db["users"] and referrer_id != str(user_id):
        if referrer_id not in db["referrals"]:
            db["referrals"][referrer_id] = []
        if str(user_id) not in db["referrals"][referrer_id]:
            db["referrals"][referrer_id].append(str(user_id))
            db["users"][referrer_id]["coins"] += 500
            save_db(db)
            try:
                await bot.send_message(chat_id=int(referrer_id), text=f"🎉 @{username} taklifingiz bo'yicha qo'shildi! Sizga **+500 Coin** berildi.")
            except:
                pass

    kb_buttons = []
    if WEBAPP_URL:
        kb_buttons.append([InlineKeyboardButton(text="🚀 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons) if kb_buttons else None
    await message.answer("👋 Cyber Pro Hub botiga xush kelibsiz!", reply_markup=kb)

# ----------------- API ENDPOINTS -----------------
@app.get("/api/get_user")
async def get_user(user_id: int):
    init_user(user_id)
    db = update_user_energy(user_id)
    str_id = str(user_id)
    u = db["users"][str_id]

    refs_count = len(db["referrals"].get(str_id, []))
    
    # Bot username'ini xavfsiz olish
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception:
        bot_username = "@kunlik_vazifalar_2026_bot" # ⚠️ Shu yerga botingizning haqiqiy usename'ini yozib qo'ying (masalan: CyberPro_bot)

    return {
        "success": True,
        "coins": u["coins"],
        "energy": u["energy"],
        "max_energy": u["max_energy"],
        "tap_level": u["tap_level"],
        "wallet": u.get("wallet", ""),
        "is_admin": (user_id == ADMIN_ID or ADMIN_ID == 0),
        "ref_count": refs_count,
        "ref_link": f"https://t.me/{bot_username}?start={user_id}",
        "completed_tasks": db["completed_tasks"].get(str_id, []),
        "last_daily_claim": db["daily_claims"].get(str_id, 0),
        "tasks": TASKS
    }
@app.post("/api/tap")
async def tap_coin(data: CoinModel):
    init_user(data.user_id)
    db = update_user_energy(data.user_id)
    str_id = str(data.user_id)
    u = db["users"][str_id]

    tap_power = u.get("tap_level", 1)
    if u["energy"] < tap_power:
        return {"success": False, "message": "Energiya yetarli emas!"}

    u["coins"] += tap_power
    u["energy"] -= tap_power
    u["taps_count"] = u.get("taps_count", 0) + 1
    save_db(db)

    return {"success": True, "new_balance": u["coins"], "energy": u["energy"]}

@app.post("/api/buy_boost")
async def buy_boost(data: BoostModel):
    db = load_db()
    str_id = str(data.user_id)
    u = db["users"].get(str_id)

    if not u:
        return {"success": False, "message": "User topilmadi!"}

    if data.boost_type == "multitap":
        cost = u.get("tap_level", 1) * 1000
        if u["coins"] < cost:
            return {"success": False, "message": f"Tangalar yetarli emas! Narxi: {cost} Coin"}
        u["coins"] -= cost
        u["tap_level"] = u.get("tap_level", 1) + 1
        save_db(db)
        return {"success": True, "message": f"🚀 Multitap LVL {u['tap_level']} oshirildi!"}

    elif data.boost_type == "max_energy":
        cost = (u.get("max_energy", 1000) // 500) * 1500
        if u["coins"] < cost:
            return {"success": False, "message": f"Tangalar yetarli emas! Narxi: {cost} Coin"}
        u["coins"] -= cost
        u["max_energy"] = u.get("max_energy", 1000) + 500
        save_db(db)
        return {"success": True, "message": f"⚡️ Max energiya {u['max_energy']} ga oshirildi!"}

    return {"success": False, "message": "Noma'lum boost!"}

@app.post("/api/connect_wallet")
async def connect_wallet(data: WalletModel):
    db = load_db()
    str_id = str(data.user_id)
    if str_id in db["users"]:
        db["users"][str_id]["wallet"] = data.wallet_address
        save_db(db)
        return {"success": True, "message": "💎 TON Hamyon saqlandi!"}
    return {"success": False, "message": "User topilmadi!"}

@app.post("/api/claim_daily")
async def claim_daily(data: CoinModel):
    db = load_db()
    str_id = str(data.user_id)
    now_ts = int(datetime.now().timestamp())
    last_ts = db["daily_claims"].get(str_id, 0)

    if now_ts - last_ts < 86400:
        return {"success": False, "message": "Vaqt hali to'lmadi! Taymerni kuting."}

    reward = 500
    db["users"][str_id]["coins"] += reward
    db["daily_claims"][str_id] = now_ts
    save_db(db)

    return {"success": True, "message": f"🎁 +{reward} Coin kunlik bonus olindi!"}

@app.post("/api/complete_task")
async def complete_task(data: TaskModel):
    db = load_db()
    str_id = str(data.user_id)
    
    if str_id not in db["completed_tasks"]:
        db["completed_tasks"][str_id] = []

    if data.task_id in db["completed_tasks"][str_id]:
        return {"success": False, "message": "Bu vazifa allaqachon bajarilgan!"}

    target = next((t for t in TASKS if t["id"] == data.task_id), None)
    if not target:
        return {"success": False, "message": "Vazifa topilmadi!"}

    db["completed_tasks"][str_id].append(data.task_id)
    db["users"][str_id]["coins"] += target["reward"]
    save_db(db)

    return {"success": True, "message": f"✅ +{target['reward']} Coin berildi!"}

@app.get("/api/leaderboard")
async def get_leaderboard():
    db = load_db()
    sorted_users = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    top_list = [{"rank": r, "username": u[1].get("username", "User"), "coins": u[1].get("coins", 0)} for r, u in enumerate(sorted_users, start=1)]
    return {"success": True, "leaderboard": top_list}

@app.get("/api/admin/stats")
async def get_admin_stats(user_id: int):
    db = load_db()
    user_list = [{"user_id": uid, "username": udata.get("username", "User"), "coins": udata.get("coins", 0), "wallet": udata.get("wallet", "")} for uid, udata in db["users"].items()]

    return {
        "success": True,
        "stats": {
            "total_users": len(db["users"]),
            "total_coins": sum(u["coins"] for u in db["users"].values()),
            "total_refs": sum(len(refs) for refs in db["referrals"].values())
        },
        "users": user_list
    }

@app.post("/api/admin/send_direct")
async def admin_send_direct(data: DirectMsgModel):
    if ADMIN_ID != 0 and data.admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat berilmadi!"}
    try:
        await bot.send_message(chat_id=data.target_user_id, text=f"💬 **Admin xabari:**\n\n{data.message}")
        return {"success": True, "message": "Xabar yuborildi!"}
    except Exception as e:
        return {"success": False, "message": f"Xatolik: {str(e)}"}

@app.post("/api/admin/broadcast")
async def admin_broadcast(data: BroadcastMsgModel):
    if ADMIN_ID != 0 and data.admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat berilmadi!"}
    db = load_db()
    count = 0
    for uid in list(db["users"].keys()):
        try:
            await bot.send_message(chat_id=int(uid), text=f"📢 **E'lon:**\n\n{data.message}")
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    return {"success": True, "message": f"{count} ta foydalanuvchiga yetkazildi!"}

async def main():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
