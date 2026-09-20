import json
import os
import time

DB_FILE = "database.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_or_create_user(user_id, username="O'yinchi", ref_by=None):
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
            "is_vip": False,
            "theme": "default",
            "auto_bot": False,
            "last_auto_bot": current_time,
            "last_energy_update": current_time,
            "last_daily_claim": 0,
            "completed_tasks": []
        }
        if ref_by and str(ref_by) != str_user_id and str(ref_by) in data:
            data[str(ref_by)]["score"] += 1000
        save_data(data)

    user = data[str_user_id]
    
    # Auto-bot (Passiv daromad)
    if user.get("auto_bot"):
        passed = current_time - user.get("last_auto_bot", current_time)
        earned = min(passed, 10800) # Max 3 soat = 10800 coin
        if earned > 0:
            user["score"] += earned
            user["last_auto_bot"] = current_time

    # Energiya qayta tiklanishi
    regen_rate = 1 if user.get('is_vip') else 2
    time_passed = current_time - user['last_energy_update']
    energy_to_add = time_passed // regen_rate

    if energy_to_add > 0 and user['energy'] < user['max_energy']:
        user['energy'] = min(user['max_energy'], user['energy'] + energy_to_add)
        user['last_energy_update'] = current_time

    save_data(data)
    return user

def process_tap(user_id, tap_count=1):
    data = load_data()
    str_user_id = str(user_id)
    current_time = int(time.time())

    if str_user_id not in data:
        get_or_create_user(user_id)
        data = load_data()

    user = data[str_user_id]
    total_power = user['tap_power'] * tap_count
    
    if user['energy'] >= total_power:
        user['score'] += total_power
        user['total_taps'] = user.get('total_taps', 0) + tap_count
        user['energy'] -= total_power
        user['last_energy_update'] = current_time
        save_data(data)
        return {"success": True, "score": user['score'], "energy": user['energy']}
    return {"success": False, "error": "Energiya tugadi"}

def claim_daily(user_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data: return {"success": False, "message": "Topilmadi"}

    user = data[str_user_id]
    current_time = int(time.time())
    last_claim = user.get("last_daily_claim", 0)

    if current_time - last_claim >= 86400:
        user["score"] += 1500
        user["last_daily_claim"] = current_time
        save_data(data)
        return {"success": True, "message": "🎁 Kunlik bonus: +1,500 Coin!"}
    else:
        hours_left = int((86400 - (current_time - last_claim)) // 3600)
        return {"success": False, "message": f"Kuting: {hours_left} soat qoldi."}

def complete_task(user_id, task_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data: return {"success": False, "message": "Topilmadi"}

    user = data[str_user_id]
    completed = user.get("completed_tasks", [])

    if task_id in completed:
        return {"success": False, "message": "Vazifa allaqachon bajarilgan!"}

    reward = 2000
    user["score"] += reward
    completed.append(task_id)
    user["completed_tasks"] = completed
    save_data(data)
    return {"success": True, "message": f"✅ Vazifa bajarildi! +{reward} Coin"}

def buy_boost(user_id, boost_type):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id not in data: return {"success": False, "message": "Topilmadi"}
    
    user = data[str_user_id]
    
    if boost_type == "energy_500":
        if user['score'] >= 50:
            user['score'] -= 50
            user['max_energy'] += 500
            user['energy'] = user['max_energy']
            save_data(data)
            return {"success": True, "message": "⚡ Energiya +500 ga oshdi!"}
        return {"success": False, "message": "Tangalar yetarli emas!"}

    elif boost_type == "tap_power":
        cost = user['tap_power'] * 200
        if user['score'] >= cost:
            user['score'] -= cost
            user['tap_power'] += 1
            save_data(data)
            return {"success": True, "message": "🚀 Tap kuchi oshdi!"}
        return {"success": False, "message": f"Tangalar yetarli emas ({cost} 🪙)"}

    elif boost_type == "auto_bot":
        if user.get("auto_bot"): return {"success": False, "message": "Auto-bot yoqilgan!"}
        if user['score'] >= 3000:
            user['score'] -= 3000
            user['auto_bot'] = True
            user['last_auto_bot'] = int(time.time())
            save_data(data)
            return {"success": True, "message": "🤖 Auto-bot ishga tushdi!"}
        return {"success": False, "message": "Auto-bot uchun 3,000 Coin kerak!"}

    return {"success": False, "message": "Xatolik"}

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
