import sqlite3
import time

DB_NAME = "cyber_pro_hub.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 1000,
            max_energy INTEGER DEFAULT 1000,
            referrer_id INTEGER,
            autotap_level INTEGER DEFAULT 0,
            last_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tranzaksiyalar va Xaridlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tx_hash TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            item_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Dastur ishga tushganda bazani yaratish
init_db()

def get_or_create_user(user_id, username="User", referrer_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, referrer_id, last_active) VALUES (?, ?, ?, ?)",
            (user_id, username, referrer_id, int(time.time()))
        )
        conn.commit()
        
        # Referal bonusini berish (agar taklif qiluvchi bo'lsa)
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET coins = coins + 5000 WHERE user_id = ?", (referrer_id,))
            conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return dict(user)

def update_user_tap(user_id, coins_added, energy_used):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or user["energy"] < energy_used:
        conn.close()
        return False
        
    new_coins = user["coins"] + coins_added
    new_energy = user["energy"] - energy_used
    
    cursor.execute(
        "UPDATE users SET coins = ?, energy = ?, last_active = ? WHERE user_id = ?",
        (new_coins, new_energy, int(time.time()), user_id)
    )
    conn.commit()
    conn.close()
    return True

def process_ton_purchase(user_id, tx_hash, amount, item_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (user_id, tx_hash, amount, item_type) VALUES (?, ?, ?, ?)",
            (user_id, tx_hash, amount, item_type)
        )
        
        if item_type == "BUY_COINS":
            coins_to_add = int(amount * 1000000)
            cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins_to_add, user_id))
        elif item_type == "AUTOTAP_BOT":
            cursor.execute("UPDATE users SET autotap_level = autotap_level + 1 WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()
        return True, "Xarid muvaffaqiyatli bajarildi!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Bu tranzaksiya ishlatilgan!"
    except Exception as e:
        conn.close()
        return False, f"Xatolik: {str(e)}"

def get_admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_users, SUM(coins) as total_coins FROM users")
    stats = cursor.fetchone()
    conn.close()
    return dict(stats) if stats else {"total_users": 0, "total_coins": 0}
