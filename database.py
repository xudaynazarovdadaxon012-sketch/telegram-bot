import sqlite3
from datetime import datetime, timedelta

def init_db():
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

def claim_daily_streak(user_id: int):
    """Kunlik bonus olish tizimi (Kam error beruvchi mantiq)"""
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_streak, streak_days FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    today = datetime.now().date()
    
    if not row or not row[0]:
        # Birinchi marta kirishi
        cursor.execute("UPDATE users SET coins = coins + 50, streak_days = 1, last_streak = ? WHERE user_id = ?", (str(today), user_id))
        conn.commit()
        conn.close()
        return True, 1, 50
    
    last_date = datetime.strptime(row[0], "%Y-%m-%d").date()
    streak = row[1]
    
    if last_date == today:
        conn.close()
        return False, streak, 0 # Bugun olib bo'lgan
        
    if last_date == today - timedelta(days=1):
        streak += 1 # Ketma-ket kun
    else:
        streak = 1 # Kun o'tib ketgan bo'lsa qayta 1-kundan boshlanadi
        
    reward = streak * 50 # Har bir kun uchun oshib boradi (50, 100, 150...)
    cursor.execute("UPDATE users SET coins = coins + ?, streak_days = ?, last_streak = ? WHERE user_id = ?", (reward, streak, str(today), user_id))
    conn.commit()
    conn.close()
    return True, streak, reward
