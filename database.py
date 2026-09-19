import sqlite3
import time

DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                tap_power INTEGER DEFAULT 1,
                last_energy_update INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

init_db()

def get_or_create_user(user_id, username="O'yinchi", ref_by=None):
    current_time = int(time.time())
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute('''
                INSERT INTO users (user_id, username, last_energy_update)
                VALUES (?, ?, ?)
            ''', (user_id, username, current_time))
            
            if ref_by and str(ref_by) != str(user_id):
                cursor.execute('UPDATE users SET score = score + 1000 WHERE user_id = ?', (ref_by,))
                
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()

        user = dict(user)
        time_passed = current_time - user['last_energy_update']
        energy_to_add = time_passed // 3

        if energy_to_add > 0 and user['energy'] < user['max_energy']:
            new_energy = min(user['max_energy'], user['energy'] + energy_to_add)
            cursor.execute('''
                UPDATE users SET energy = ?, last_energy_update = ? WHERE user_id = ?
            ''', (new_energy, current_time, user_id))
            conn.commit()
            user['energy'] = new_energy

        return user

def process_tap(user_id):
    current_time = int(time.time())
    with get_connection() as conn:
        cursor = conn.cursor()
        user = get_or_create_user(user_id)

        if user['energy'] >= user['tap_power']:
            new_score = user['score'] + user['tap_power']
            new_energy = user['energy'] - user['tap_power']
            
            cursor.execute('''
                UPDATE users 
                SET score = ?, energy = ?, last_energy_update = ? 
                WHERE user_id = ?
            ''', (new_score, new_energy, current_time, user_id))
            conn.commit()
            return {"success": True, "score": new_score, "energy": new_energy}
        else:
            return {"success": False, "error": "Energiya yetarli emas"}

def update_score(user_id, score_change):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET score = score + ? WHERE user_id = ?', (score_change, user_id))
        conn.commit()
