import json
import os
import time

DB_FILE = "database.json"

# Oddiy faylni o'qish funksiyasi
def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# Faylga saqlash funksiyasi
def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Foydalanuvchini olish yoki yaratish
def get_or_create_user(user_id, username="O'yinchi"):
    data = load_data()
    str_user_id = str(user_id)
    current_time = int(time.time())

    if str_user_id not in data:
        data[str_user_id] = {
            "user_id": user_id,
            "username": username,
            "score": 0,
            "total_taps": 0,
            "energy": 100,
            "max_energy": 100,
            "tap_power": 1,
            "auto_bot": False,
            "last_auto_bot": current_time,
            "last_energy_update": current_time,
            "last_daily_claim": 0,
            "completed_tasks": [],
            "theme": "default"
        }
        save_data(data)

    user = data[str_user_id]

    # Auto-bot (Passiv daromad)
    if user.get("auto_bot"):
        passed = current_time - user.get("last_auto_bot", current_time)
        earned = min(passed, 10800) # Max 3 soat
        if earned > 0:
            user["score"] += earned
            user["last_auto_bot"] = current_time

    # Energiya tiklanishi
    time_passed = current_time - user['last_energy_update']
    energy_to_add = time_passed // 2 # Har 2 sekundda 1 energiya

    if energy_to_add > 0 and user['energy'] < user['max_energy']:
        user['energy'] = min(user['max_energy'], user['energy'] + energy_to_add)
        user['last_energy_update'] = current_time

    save_data(data)
    return user

# Tap bosish
def process_tap(user_id, tap_count=1):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data:
        get_or_create_user(user_id)
        data = load_data()

    user = data[str_user_id]
    total_power = user['tap_power'] * tap_count

    if user['energy'] >= total_power:
        user['score'] += total_power
        user['total_taps'] = user.get('total_taps', 0) + tap_count
        user['energy'] -= total_power
        user['last_energy_update'] = int(time.time())
        save_data(data)
        return {"success": True, "score": user['score'], "energy": user['energy']}
    return {"success": False, "error": "Energiya tugadi"}

# Kunlik bonus (+100 🪙)
def claim_daily(user_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data: 
        return {"success": False, "message": "Foydalanuvchi topilmadi"}

    user = data[str_user_id]
    current_time = int(time.time())
    last_claim = user.get("last_daily_claim", 0)

    if current_time - last_claim >= 86400:
        user["score"] += 100
        user["last_daily_claim"] = current_time
        save_data(data)
        return {"success": True, "message": "🎁 Kunlik bonus: +100 Coin!"}
    else:
        hours_left = int((86400 - (current_time - last_claim)) // 3600)
        return {"success": False, "message": f"Kuting: {hours_left} soat qoldi."}

# Do'kondagi buyumlar (100 🪙, 50 🪙, 300 🪙)
def buy_boost(user_id, boost_type):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data: 
        return {"success": False, "message": "Foydalanuvchi topilmadi"}

    user = data[str_user_id]

    if boost_type == "energy_500":
        if user['score'] >= 50:
            user['score'] -= 50
            user['max_energy'] += 50
            user['energy'] = user['max_energy']
            save_data(data)
            return {"success": True, "message": "⚡ Energiya +50 ga oshirildi!"}
        return {"success": False, "message": "Tangalaringiz yetarli emas (50 🪙)!"}

    elif boost_type == "tap_power":
        cost = user['tap_power'] * 100
        if user['score'] >= cost:
            user['score'] -= cost
            user['tap_power'] += 1
            save_data(data)
            return {"success": True, "message": "🚀 Tap kuchi oshirildi!"}
        return {"success": False, "message": f"Tangalar yetarli emas ({cost} 🪙)!"}

    elif boost_type == "auto_bot":
        if user.get("auto_bot"): 
            return {"success": False, "message": "Auto-bot allaqachon yoqilgan!"}
        if user['score'] >= 300:
            user['score'] -= 300
            user['auto_bot'] = True
            user['last_auto_bot'] = int(time.time())
            save_data(data)
            return {"success": True, "message": "🤖 Auto-bot ishga tushirildi!"}
        return {"success": False, "message": "Auto-bot uchun 300 Coin kerak!"}

    return {"success": False, "message": "Xatolik yuz berdi"}

# Telegram Stars Exchange (5,000 Coin = 5 Stars)
def exchange_coins_for_stars(user_id, stars_amount=5):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data:
        return {"success": False, "message": "Foydalanuvchi topilmadi"}

    user = data[str_user_id]
    required_coins = stars_amount * 1000

    if user['score'] >= required_coins:
        user['score'] -= required_coins
        save_data(data)
        return {"success": True, "message": f"✅ Ariza qabul qilindi! {stars_amount} Telegram Stars beriladi."}
    else:
        return {"success": False, "message": f"Tangalar yetarli emas! {stars_amount} Stars uchun {required_coins} 🪙 kerak."}

def set_theme(user_id, theme_name):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id in data:
        data[str_user_id]["theme"] = theme_name
        save_data(data)
        return {"success": True}
    return {"success": False}

def get_leaderboard():
    data = load_data()
    users = list(data.values())
    users.sort(key=lambda x: x.get('score', 0), reverse=True)
    return users[:10]
