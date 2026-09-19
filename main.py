import sqlite3
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Front-end va Back-end o'rtasidagi so'rovlar uchun

DB_NAME = "game_database.db"

# Ma'lumotlar bazasini yaratish va sozlash
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            score INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100,
            max_energy INTEGER DEFAULT 100,
            tap_power INTEGER DEFAULT 1,
            quiz_index INTEGER DEFAULT 0,
            last_energy_update REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Foydalanuvchi ma'lumotlarini yuklash / yaratish
@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json
    user_id = str(data.get('userId'))
    username = data.get('username', "O'yinchi")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    now = time.time()

    if user is None:
        cursor.execute('''
            INSERT INTO users (user_id, username, score, energy, max_energy, tap_power, quiz_index, last_energy_update)
            VALUES (?, ?, 0, 100, 100, 1, 0, ?)
        ''', (user_id, username, now))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    else:
        # Avto-energiya tiklanishini hisoblash (har 3 soniyada +1 energiya)
        time_passed = now - user['last_energy_update']
        energy_to_add = int(time_passed // 3)
        if energy_to_add > 0 and user['energy'] < user['max_energy']:
            new_energy = min(user['max_energy'], user['energy'] + energy_to_add)
            cursor.execute('UPDATE users SET energy = ?, last_energy_update = ? WHERE user_id = ?', (new_energy, now, user_id))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()

    user_data = dict(user)
    conn.close()
    return jsonify({"success": True, "user": user_data})

# 2. Tap bosilganda hisoblash
@app.route('/api/user/tap', methods=['POST'])
def handle_tap():
    data = request.json
    user_id = str(data.get('userId'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404

    if user['energy'] >= 1:
        new_score = user['score'] + user['tap_power']
        new_energy = user['energy'] - 1
        cursor.execute('UPDATE users SET score = ?, energy = ? WHERE user_id = ?', (new_score, new_energy, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "score": new_score, "energy": new_energy})
    
    conn.close()
    return jsonify({"success": False, "error": "Energiya yetarli emas"}), 400

# 3. Spin (Omadli G'ildirak) hisoblash
@app.route('/api/user/spin', methods=['POST'])
def handle_spin():
    data = request.json
    user_id = str(data.get('userId'))
    win_amount = int(data.get('winAmount', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or user['score'] < 200:
        conn.close()
        return jsonify({"success": False, "error": "Coin yetarli emas"}), 400

    new_score = user['score'] - 200 + win_amount
    cursor.execute('UPDATE users SET score = ? WHERE user_id = ?', (new_score, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "score": new_score})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
