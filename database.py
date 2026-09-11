import sqlite3

DB_NAME = "cyber_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 1000,
            max_energy INTEGER DEFAULT 1000,
            tap_level INTEGER DEFAULT 1,
            wallet TEXT DEFAULT '',
            last_daily_claim TEXT DEFAULT '',
            completed_tasks TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

# Baza jadvalini yaratish
init_db()

def get_or_create_user(user_id, username="User"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, username, coins, energy, max_energy, tap_level, wallet, last_daily_claim, completed_tasks)
            VALUES (?, ?, 0, 1000, 1000, 1, '', '', '')
        ''', (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

    conn.close()
    return {
        "user_id": user[0],
        "username": user[1],
        "coins": user[2],
        "energy": user[3],
        "max_energy": user[4],
        "tap_level": user[5],
        "wallet": user[6],
        "last_daily_claim": user[7],
        "completed_tasks": user[8].split(",") if user[8] else []
    }

def update_user_tap(user_id, coins_added, energy_used):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[1] < energy_used:
        conn.close()
        return False

    new_coins = row[0] + coins_added
    new_energy = row[1] - energy_used
    cursor.execute("UPDATE users SET coins = ?, energy = ? WHERE user_id = ?", (new_coins, new_energy, user_id))
    conn.commit()
    conn.close()
    return True

def update_user_wallet(user_id, wallet_address):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET wallet = ? WHERE user_id = ?", (wallet_address, user_id))
    conn.commit()
    conn.close()

def buy_boost_upgrade(user_id, boost_type, cost):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coins, tap_level, max_energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row or row[0] < cost:
        conn.close()
        return False, "Tangalar yetarli emas!"

    new_coins = row[0] - cost
    if boost_type == 'multitap':
        cursor.execute("UPDATE users SET coins = ?, tap_level = tap_level + 1 WHERE user_id = ?", (new_coins, user_id))
    elif boost_type == 'max_energy':
        cursor.execute("UPDATE users SET coins = ?, max_energy = max_energy + 500, energy = energy + 500 WHERE user_id = ?", (new_coins, user_id))

    conn.commit()
    conn.close()
    return True, "Muvaffaqiyatli oshirildi!"

def claim_daily_bonus(user_id, reward=1000):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    return True, "Kunlik bonus olindi!"

def complete_user_task(user_id, task_id, reward):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT completed_tasks, coins FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    completed = row[0].split(",") if row[0] else []
    if task_id in completed:
        conn.close()
        return False, "Vazifa allaqachon bajarilgan!"

    completed.append(task_id)
    new_completed_str = ",".join(completed)
    new_coins = row[1] + reward

    cursor.execute("UPDATE users SET completed_tasks = ?, coins = ? WHERE user_id = ?", (new_completed_str, new_coins, user_id))
    conn.commit()
    conn.close()
    return True, "Vazifa bajarildi va mukofot berildi!"

def get_top_leaderboard(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, coins FROM users ORDER BY coins DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"username": r[0], "coins": r[1]} for r in rows]

def get_admin_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(coins) FROM users")
    row = cursor.fetchone()
    
    cursor.execute("SELECT user_id, username, coins, wallet FROM users ORDER BY coins DESC LIMIT 20")
    users = cursor.fetchall()
    conn.close()

    total_users = row[0] if row else 0
    total_coins = row[1] if row and row[1] else 0

    return {
        "posts": total_users,
        "followers": total_coins,
        "following": 1,
        "bio": "Cyber Pro Hub Official Backend Status: ONLINE 🟢",
        "users": [{"user_id": u[0], "username": u[1], "coins": u[2], "wallet": u[3]} for u[u in users]] if users else []
    }

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]
