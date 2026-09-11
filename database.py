import sqlite3
from datetime import datetime, timedelta

def init_db():
    """Ma'lumotlar bazasini yaratish"""
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            coins INTEGER DEFAULT 0,
            invited_count INTEGER DEFAULT 0,
            last_streak TEXT,
            streak_days INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, referrer_id: int = None):
    """Foydalanuvchini olish yoki yangi qo'shish"""
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, coins, invited_count FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, referrer_id, coins, invited_count) VALUES (?, ?, ?, ?)",
            (user_id, referrer_id, 0, 0)
        )
        
        if referrer_id and referrer_id != user_id:
            cursor.execute(
                "UPDATE users SET coins = coins + 100, invited_count = invited_count + 1 WHERE user_id = ?",
                (referrer_id,)
            )
            
        conn.commit()
        cursor.execute("SELECT user_id, coins, invited_count FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def claim_daily_streak(user_id: int):
    """Kunlik bonus olish"""
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_streak, streak_days FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    today = datetime.now().date()
    
    if not row or not row[0]:
        cursor.execute("UPDATE users SET coins = coins + 50, streak_days = 1, last_streak = ? WHERE user_id = ?", (str(today), user_id))
        conn.commit()
        conn.close()
        return True, 1, 50
    
    last_date = datetime.strptime(row[0], "%Y-%m-%d").date()
    streak = row[1]
    
    if last_date == today:
        conn.close()
        return False, streak, 0
        
    if last_date == today - timedelta(days=1):
        streak += 1
    else:
        streak = 1
        
    reward = streak * 50
    cursor.execute("UPDATE users SET coins = coins + ?, streak_days = ?, last_streak = ? WHERE user_id = ?", (reward, streak, str(today), user_id))
    conn.commit()
    conn.close()
    return True, streak, reward
