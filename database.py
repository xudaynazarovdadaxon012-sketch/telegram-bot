import sqlite3

DB_NAME = "database.db"

def init_db():
    """Ma'lumotlar bazasi va jadvalni yaratish"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id TEXT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 500,
            pushups INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user_data(tg_id):
    """Foydalanuvchi ma'lumotlarini olish yoki yangi ochish"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT score, energy, pushups FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (tg_id, score, energy, pushups) VALUES (?, 0, 500, 0)", (tg_id,))
        conn.commit()
        user = (0, 500, 0)
        
    conn.close()
    return {'score': user[0], 'energy': user[1], 'pushups': user[2]}

def update_user_data(tg_id, score, energy, pushups):
    """Ma'lumotlarni bazada yangilash"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET score = ?, energy = ?, pushups = ? WHERE tg_id = ?
    """, (score, energy, pushups, tg_id))
    conn.commit()
    conn.close()

def deduct_score(tg_id, cost):
    """Stars so'rovi uchun coin yechib olish"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    
    if user and user[0] >= cost:
        new_score = user[0] - cost
        cursor.execute("UPDATE users SET score = ? WHERE tg_id = ?", (new_score, tg_id))
        conn.commit()
        conn.close()
        return new_score
    
    conn.close()
    return None
