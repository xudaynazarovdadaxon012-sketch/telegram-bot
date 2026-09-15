import os
import random
import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='.')

# --- ADMIN ID LAR RO'YXATI ---
ADMIN_IDS = [8898979946]  # O'zingizning Telegram ID'ingizni shu yerga yozing

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- BAZANI SOZLASH ---
def init_db():
    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 1000,
            referred_by INTEGER,
            cases_opened INTEGER DEFAULT 0
        )
    ''')
    
    # Homiy kanallar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_username TEXT,
            is_mandatory BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

# --- 1. USER INIT & REFERRAL ( Do'st taklif qilish: +100 tanga ) ---
@app.route('/api/start', methods=['POST'])
def start_game():
    data = request.json or {}
    user_id = data.get('user_id')
    username = data.get('username', '')
    ref_id = data.get('ref_id')

    if not user_id:
        return jsonify({"status": "error", "message": "User ID topilmadi"}), 400

    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, energy FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        referred_by = None
        if ref_id and str(ref_id).isdigit() and int(ref_id) != int(user_id):
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (int(ref_id),))
            if cursor.fetchone():
                referred_by = int(ref_id)
                # Taklif qilganga +100 tanga
                cursor.execute('UPDATE users SET balance = balance + 100 WHERE user_id = ?', (referred_by,))

        cursor.execute('''
            INSERT INTO users (user_id, username, balance, referred_by)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, 50 if referred_by else 0, referred_by))
        conn.commit()
        balance, energy = (50 if referred_by else 0), 1000
    else:
        balance, energy = user[0], user[1]

    conn.close()

    return jsonify({
        "status": "success",
        "balance": balance,
        "energy": energy,
        "is_admin": is_admin(int(user_id)),
        "ref_link": f"https://t.me/ClickerGoldBot?start={user_id}"
    })

# --- 2. MAJBURIY KANALLARNI TEKSHIRISH ---
@app.route('/api/check_sub', methods=['POST'])
def check_sub():
    data = request.json or {}
    user_id = data.get('user_id')

    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_username FROM channels WHERE is_mandatory = 1')
    mandatory_channels = [row[0] for row in cursor.fetchall()]
    conn.close()

    # REAL PROD: Telegram Bot API (getChatMember) yordamida har bir kanal tekshiriladi
    return jsonify({
        "status": "success",
        "is_subscribed": True, # Test rejimida True
        "mandatory_channels": mandatory_channels
    })

# --- 3. 10+ SEKTORLI OMADLI G'ILDIRAK ---
@app.route('/api/spin_wheel', methods=['POST'])
def spin_wheel():
    data = request.json or {}
    user_id = data.get('user_id')
    spin_type = data.get('spin_type', 'coin') # 'coin' yoki 'stars'

    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "User topilmadi"}), 404

    # 11 ta Sektor (Minuslar ham bor)
    sectors = [
        {"id": 0, "name": "+50 Tanga", "type": "coin", "value": 50, "weight": 25},
        {"id": 1, "name": "+100 Tanga", "type": "coin", "value": 100, "weight": 20},
        {"id": 2, "name": "+250 Tanga", "type": "coin", "value": 250, "weight": 15},
        {"id": 3, "name": "+500 Tanga", "type": "coin", "value": 500, "weight": 10},
        {"id": 4, "name": "+1000 Tanga", "type": "coin", "value": 1000, "weight": 5},
        {"id": 5, "name": "Bronza Quti", "type": "box", "value": "bronze", "weight": 8},
        {"id": 6, "name": "Kumush Quti", "type": "box", "value": "silver", "weight": 5},
        {"id": 7, "name": "1 Stars", "type": "stars", "value": 1, "weight": 3},
        {"id": 8, "name": "-50 Tanga (Minus)", "type": "coin", "value": -50, "weight": 4},
        {"id": 9, "name": "-100 Tanga (Minus)", "type": "coin", "value": -100, "weight": 3},
        {"id": 10, "name": "Afsonaviy Quti", "type": "box", "value": "legendary", "weight": 2}
    ]

    chosen = random.choices(sectors, weights=[s["weight"] for s in sectors], k=1)[0]

    if chosen["type"] == "coin":
        cursor.execute('UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ?', (chosen["value"], user_id))
        conn.commit()

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "status": "success",
        "prize": chosen,
        "new_balance": new_balance
    })

# --- 4. CS:GO USLUBIDAGI 4 XIL QUTILAR ---
@app.route('/api/open_case', methods=['POST'])
def open_case():
    data = request.json or {}
    user_id = data.get('user_id')
    case_type = data.get('case_type') # bronze, silver, gold, legendary

    cases_config = {
        "bronze": {
            "price_type": "coin", "price": 500,
            "rewards": [
                {"name": "+100 Tanga", "type": "coin", "val": 100, "w": 40},
                {"name": "+250 Tanga", "type": "coin", "val": 250, "w": 30},
                {"name": "+400 Tanga", "type": "coin", "val": 400, "w": 15},
                {"name": "-50 Tanga (Minus)", "type": "coin", "val": -50, "w": 10},
                {"name": "+100 Energiya", "type": "energy", "val": 100, "w": 5}
            ]
        },
        "silver": {
            "price_type": "coin", "price": 2000,
            "rewards": [
                {"name": "+800 Tanga", "type": "coin", "val": 800, "w": 40},
                {"name": "+1500 Tanga", "type": "coin", "val": 1500, "w": 35},
                {"name": "+2500 Tanga", "type": "coin", "val": 2500, "w": 15},
                {"name": "-200 Tanga (Minus)", "type": "coin", "val": -200, "w": 5},
                {"name": "1 Stars", "type": "stars", "val": 1, "w": 5}
            ]
        },
        "gold": {
            "price_type": "stars", "price": 1,
            "rewards": [
                {"name": "+5000 Tanga", "type": "coin", "val": 5000, "w": 50},
                {"name": "+10000 Tanga", "type": "coin", "val": 10000, "w": 30},
                {"name": "2 Stars", "type": "stars", "val": 2, "w": 15},
                {"name": "5 Stars", "type": "stars", "val": 5, "w": 5}
            ]
        },
        "legendary": {
            "price_type": "stars", "price": 5,
            "rewards": [
                {"name": "+50000 Tanga", "type": "coin", "val": 50000, "w": 40},
                {"name": "10 Stars", "type": "stars", "val": 10, "w": 35},
                {"name": "50 Stars", "type": "stars", "val": 50, "w": 20},
                {"name": "100 Stars (JACKPOT)", "type": "stars", "val": 100, "w": 5}
            ]
        }
    }

    if case_type not in cases_config:
        return jsonify({"status": "error", "message": "Noma'lum quti"}), 400

    cfg = cases_config[case_type]
    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "User topilmadi"}), 404

    current_balance = user[0]

    if cfg["price_type"] == "coin":
        if current_balance < cfg["price"]:
            conn.close()
            return jsonify({"status": "error", "message": "Tangalaringiz yetarli emas!"}), 400
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (cfg["price"], user_id))

    reward = random.choices(cfg["rewards"], weights=[r["w"] for r in cfg["rewards"]], k=1)[0]

    if reward["type"] == "coin":
        cursor.execute('UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ?', (reward["val"], user_id))

    cursor.execute('UPDATE users SET cases_opened = cases_opened + 1 WHERE user_id = ?', (user_id,))
    conn.commit()

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "status": "success",
        "reward": reward,
        "new_balance": new_balance
    })

# --- 5. ADMIN PANEL API ---
@app.route('/api/admin/add_channel', methods=['POST'])
def add_channel():
    data = request.json or {}
    user_id = data.get('user_id')
    channel_username = data.get('channel_username')

    if not is_admin(int(user_id)):
        return jsonify({"status": "error", "message": "Admin emassiz!"}), 403

    conn = sqlite3.connect('clicker_gold.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO channels (channel_id, channel_username, is_mandatory) VALUES (?, ?, 1)',
                   (channel_username, channel_username))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Kanal qo'shildi!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
