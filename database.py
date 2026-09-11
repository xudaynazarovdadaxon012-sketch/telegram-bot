import sqlite3

def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            coins INTEGER DEFAULT 0,
            invited_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, referrer_id: int = None):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, coins, invited_count FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Yangi foydalanuvchini qo'shish (ro'yxatdan o'tganiga 50 coin bonus)
        cursor.execute("INSERT INTO users (user_id, referrer_id, coins) VALUES (?, ?, ?)", (user_id, referrer_id, 50))
        
        # Taklif qilgan insonga 100 coin mukofot berish
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET coins = coins + 100, invited_count = invited_count + 1 WHERE user_id = ?", (referrer_id,))
            
        conn.commit()
        cursor.execute("SELECT user_id, coins, invited_count FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def add_coins(user_id: int, amount: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
