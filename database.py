import json
import os
from datetime import datetime

DB_FILE = "database.json"

def get_default_db():
    return {
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

def load_db():
    if not os.path.exists(DB_FILE):
        db = get_default_db()
        save_db(db)
        return db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Baza o'qishda xatolik: {e}")
        return get_default_db()

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Bazaga saqlashda xatolik: {e}")

def init_user(user_id: int, username: str = "User"):
    db = load_db()
    str_id = str(user_id)
    
    if str_id not in db["users"]:
        db["users"][str_id] = {
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
    else:
        u = db["users"][str_id]
        if "energy" not in u: u["energy"] = 1000
        if "max_energy" not in u: u["max_energy"] = 1000
        if "last_energy_update" not in u: u["last_energy_update"] = datetime.now().timestamp()
        if "tap_level" not in u: u["tap_level"] = 1
        if "wallet" not in u: u["wallet"] = ""
        
    save_db(db)
    return db

def update_user_energy(user_id: int):
    db = load_db()
    str_id = str(user_id)
    
    if str_id in db["users"]:
        u = db["users"][str_id]
        now = datetime.now().timestamp()
        passed_sec = int(now - u.get("last_energy_update", now))
        
        if passed_sec > 0:
            added_energy = passed_sec * 2
            u["energy"] = min(u.get("max_energy", 1000), u.get("energy", 1000) + added_energy)
            u["last_energy_update"] = now
            save_db(db)
            
    return db
