import sqlite3

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            score INTEGER DEFAULT 1000,
            energy INTEGER DEFAULT 1000,
            max_energy INTEGER DEFAULT 1000,
            tap_level INTEGER DEFAULT 1,
            autobot_level INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_or_create_user(tg_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(tg_id),))
    row = cursor.fetchone()

    if not row:
        cursor.execute('''
            INSERT INTO users (telegram_id, score, energy, max_energy, tap_level, autobot_level, referrals) 
            VALUES (?, 1000, 1000, 1000, 1, 0, 0)
        ''', (str(tg_id),))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(tg_id),))
        row = cursor.fetchone()

    data = dict(row)
    conn.close()
    return data

def update_user_progress(tg_id, score, energy, tap_level, max_energy):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET score = ?, energy = ?, tap_level = ?, max_energy = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    ''', (score, energy, tap_level, max_energy, str(tg_id)))
    conn.commit()
    conn.close()

def update_user_score(tg_id, new_score):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET score = ? WHERE telegram_id = ?', (new_score, str(tg_id)))
    conn.commit()
    conn.close()

def process_upgrade(tg_id, upgrade_type):
    user = get_or_create_user(tg_id)
    score = user['score']
    tap_level = user['tap_level']
    max_energy = user['max_energy']
    energy = user['energy']

    if upgrade_type == 'tap':
        cost = tap_level * 200
        if score >= cost:
            score -= cost
            tap_level += 1
    elif upgrade_type == 'energy':
        cost = (max_energy // 500) * 300
        if score >= cost:
            score -= cost
            max_energy += 500
            energy += 500

    update_user_progress(tg_id, score, energy, tap_level, max_energy)
    return get_or_create_user(tg_id)
