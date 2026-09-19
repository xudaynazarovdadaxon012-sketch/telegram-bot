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
            "energy": 100,
            "max_energy": 100,
            "tap_power": 1,
            "is_vip": False,
            "last_energy_update": current_time,
            "last_daily": 0,
            "last_ad": 0
        }
        
        if ref_by and str(ref_by) != str_user_id and str(ref_by) in data:
            data[str(ref_by)]["score"] += 1000
            
        save_data(data)

    user = data[str_user_id]
    regen_rate = 1 if user.get('is_vip') else 3
    time_passed = current_time - user['last_energy_update']
    energy_to_add = time_passed // regen_rate

    if energy_to_add > 0 and user['energy'] < user['max_energy']:
        user['energy'] = min(user['max_energy'], user['energy'] + energy_to_add)
        user['last_energy_update'] = current_time
        save_data(data)

    return user

def process_tap(user_id):
    data = load_data()
    str_user_id = str(user_id)
    current_time = int(time.time())

    if str_user_id not in data:
        get_or_create_user(user_id)
        data = load_data()

    user = data[str_user_id]

    if user['energy'] >= user['tap_power']:
        user['score'] += user['tap_power']
        user['energy'] -= user['tap_power']
        user['last_energy_update'] = current_time
        save_data(data)
        return {"success": True, "score": user['score'], "energy": user['energy']}
    else:
        return {"success": False, "error": "Energiya yetarli emas"}

def update_score_and_energy(user_id, score_change, cost=0):
    data = load_data()
    str_user_id = str(user_id)
    current_time = int(time.time())

    if str_user_id in data:
        user = data[str_user_id]
        total_change = score_change - cost
        if user['score'] + total_change < 0:
            return {"success": False, "error": "Tangalar yetarli emas"}
        
        user['score'] += total_change
        user['last_energy_update'] = current_time
        save_data(data)
        return {"success": True, "score": user['score']}
    return {"success": False}

def claim_daily(user_id):
    data = load_data()
    str_user_id = str(user_id)
    current_time = time.time()

    if str_user_id in data:
        user = data[str_user_id]
        if current_time - user.get('last_daily', 0) >= 86400:
            bonus = 1000 if user.get('is_vip') else 500
            user['score'] += bonus
            user['last_daily'] = current_time
            save_data(data)
            return {"success": True, "score": user['score'], "message": f"Kunlik bonus +{bonus} Coin berildi!"}
        return {"success": False, "message": "Kunlik bonus allaqachon olingan (24 soat kuting)!"}
    return {"success": False}

def add_ad_reward(user_id, amount=300):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id in data:
        data[str_user_id]['score'] += amount
        save_data(data)
        return {"success": True, "score": data[str_user_id]['score'], "message": f"Adsgram reklamasi ko'rildi: +{amount} Coin!"}
    return {"success": False, "message": "Foydalanuvchi topilmadi"}

def buy_vip(user_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id in data:
        user = data[str_user_id]
        if user['score'] >= 10000:
            user['score'] -= 10000
            user['is_vip'] = True
            user['tap_power'] = 5
            user['max_energy'] = 300
            user['energy'] = 300
            save_data(data)
            return {"success": True, "score": user['score'], "energy": user['energy'], "maxEnergy": user['max_energy'], "tapPower": user['tap_power'], "message": "Tabriklaymiz! VIP Status muvaffaqiyatli faollashdi!"}
        return {"success": False, "message": f"VIP sotib olish uchun 10,000 Coin kerak! Sizda: {user['score']} Coin"}
    return {"success": False, "message": "Foydalanuvchi topilmadi"}

def exchange_to_stars(user_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id in data:
        user = data[str_user_id]
        required_coins = 5000
        if user['score'] >= required_coins:
            user['score'] -= required_coins
            save_data(data)
            return {"success": True, "score": user['score'], "message": "5000 Coin muvaffaqiyatli 1 Telegram Star ga almashtirildi!"}
        return {"success": False, "message": f"Yetarli coin yo'q! 1 Star uchun 5000 Coin kerak (Sizda: {user['score']})"}
    return {"success": False, "message": "Foydalanuvchi topilmadi"}
