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

    # VIP foydalanuvchilar uchun energiya tezroq to'ladi (1 soniyada +1)
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

    user = get_or_create_user(user_id)
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

def update_score_and_energy(user_id, score_change):
    data = load_data()
    str_user_id = str(user_id)
    current_time = int(time.time())

    if str_user_id in data:
        data[str_user_id]['score'] = max(0, data[str_user_id]['score'] + score_change)
        data[str_user_id]['last_energy_update'] = current_time
        save_data(data)
        return {"success": True, "score": data[str_user_id]['score']}
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

def watch_ad(user_id):
    data = load_data()
    str_user_id = str(user_id)
    current_time = time.time()

    if str_user_id in data:
        user = data[str_user_id]
        # Har 1 minutda reklama ko'rib tanga olish imkoniyati (simulyatsiya)
        if current_time - user.get('last_ad', 0) >= 60:
            user['score'] += 300
            user['last_ad'] = current_time
            save_data(data)
            return {"success": True, "score": user['score'], "message": "Reklama ko'rildi: +300 Coin!"}
        return {"success": False, "message": "Keyingi reklamagacha 1 daqiqa kuting!"}
    return {"success": False}

def buy_vip(user_id):
    data = load_data()
    str_user_id = str(user_id)
    if str_user_id in data:
        user = data[str_user_id]
        if user['score'] >= 10000:
            user['score'] -= 10000
            user['is_vip'] = True
            user['tap_power'] = 5 # VIP larda har bosish 5 ta tanga beradi
            user['max_energy'] = 300
            save_data(data)
            return {"success": True, "score": user['score'], "message": "Tabriklaymiz! VIP Status faollashdi!"}
        return {"success": False, "message": "VIP sotib olish uchun 10,000 Coin kerak!"}
    return {"success": False}
