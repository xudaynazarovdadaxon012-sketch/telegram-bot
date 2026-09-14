import os
import time
import random
import sqlite3
import threading
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8898979946]  # Sizning Telegram ID'ingiz

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                coins INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 1000,
                max_energy INTEGER DEFAULT 1000,
                tap_level INTEGER DEFAULT 1,
                autotap_level INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

init_db()

# --- TELEGRAM BOT POLLING ---
def run_bot_polling():
    if not BOT_TOKEN:
        return
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except Exception:
        pass

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=35).json()
            if res.get("ok"):
                for result in res.get("result", []):
                    offset = result["update_id"] + 1
                    msg = result.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "")
                    username = msg.get("from", {}).get("username", "User")

                    if text and text.startswith("/start"):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": chat_id,
                            "text": f"⚡ **Cyber Pro Hub App**ga xush kelibsiz, @{username}!\n\nO'yinga kirish va tangalar yig'ish uchun tugmani bosing:",
                            "parse_mode": "Markdown",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [{"text": "🚀 Mini App'ni Ochish", "web_app": {"url": "https://telegram-bot-7n6t.onrender.com"}}]
                                ]
                            }
                        }
                        requests.post(send_url, json=payload)
        except Exception:
            time.sleep(3)

threading.Thread(target=run_bot_polling, daemon=True).start()

# --- ROUTES & APIs ---
@app.route('/')
def index():
    return render_template('miniapp.html')

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id', 0))
    except (ValueError, TypeError):
        user_id = 0

    username = data.get('username', 'User')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Noto\'g\'ri User ID'}), 400

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user:
            conn.execute(
                'INSERT INTO users (telegram_id, username, coins, energy, max_energy, tap_level, autotap_level) VALUES (?, ?, 100, 1000, 1000, 1, 0)',
                (user_id, username)
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()

        is_admin = user_id in ADMIN_IDS

        return jsonify({
            'status': 'success',
            'data': dict(user),
            'is_admin': is_admin
        })

@app.route('/api/tap', methods=['POST'])
def handle_tap():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id', 0))
    except (ValueError, TypeError):
        user_id = 0

    count = int(data.get('count', 1))

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user or user['is_banned']:
            return jsonify({'error': 'Kirish taqiqlangan'}), 403

        if user['energy'] < count:
            return jsonify({'error': 'Energiya yetarsiz'}), 400

        earned = count * user['tap_level']
        conn.execute(
            'UPDATE users SET coins = coins + ?, energy = max(0, energy - ?) WHERE telegram_id = ?',
            (earned, count, user_id)
        )
        conn.commit()
        return jsonify({'status': 'success'})

@app.route('/api/spin', methods=['POST'])
def spin_wheel():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id', 0))
    except (ValueError, TypeError):
        user_id = 0

    reward = random.choice([50, 100, 150, 200, 300])
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user or user['is_banned']:
            return jsonify({'error': 'Ruxsat berilmagan'}), 403

        conn.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?', (reward, user_id))
        conn.commit()

    return jsonify({'status': 'success', 'reward': reward})

@app.route('/api/shop/buy', methods=['POST'])
def shop_buy():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id', 0))
    except (ValueError, TypeError):
        user_id = 0

    item = data.get('item')

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user or user['is_banned']:
            return jsonify({'error': 'Foydalanuvchi topilmadi'}), 400

        if item == 'refill':
            if user['coins'] < 300:
                return jsonify({'error': 'Tangalar yetarli emas (300 🪙 kerak)'}), 400
            conn.execute('UPDATE users SET coins = coins - 300, energy = max_energy WHERE telegram_id = ?', (user_id,))
        elif item == 'multitap':
            if user['coins'] < 500:
                return jsonify({'error': 'Tangalar yetarli emas (500 🪙 kerak)'}), 400
            conn.execute('UPDATE users SET coins = coins - 500, tap_level = tap_level + 1 WHERE telegram_id = ?', (user_id,))
        elif item == 'max_energy':
            if user['coins'] < 800:
                return jsonify({'error': 'Tangalar yetarli emas (800 🪙 kerak)'}), 400
            conn.execute('UPDATE users SET coins = coins - 800, max_energy = max_energy + 500, energy = energy + 500 WHERE telegram_id = ?', (user_id,))
        else:
            return jsonify({'error': 'Noma\'lum mahsulot'}), 400

        conn.commit()
        return jsonify({'status': 'success'})

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    data = request.json or {}
    try:
        admin_id = int(data.get('admin_id', 0))
    except (ValueError, TypeError):
        admin_id = 0

    if admin_id not in ADMIN_IDS:
        return jsonify({'error': 'Ruxsat yo\'q'}), 403

    with get_db() as conn:
        users = [dict(r) for r in conn.execute('SELECT * FROM users ORDER BY coins DESC LIMIT 25').fetchall()]
        total_u = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        total_c = conn.execute('SELECT SUM(coins) as s FROM users').fetchone()['s'] or 0

    return jsonify({'status': 'success', 'stats': {'total_users': total_u, 'total_coins': total_c}, 'users': users})

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json or {}
    try:
        admin_id = int(data.get('admin_id', 0))
    except (ValueError, TypeError):
        admin_id = 0

    if admin_id not in ADMIN_IDS:
        return jsonify({'error': 'Ruxsat yo\'q'}), 403

    action = data.get('action')
    target_id = int(data.get('target_id', 0))

    with get_db() as conn:
        if action == 'ban':
            conn.execute('UPDATE users SET is_banned = 1 WHERE telegram_id = ?', (target_id,))
        elif action == 'unban':
            conn.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (target_id,))
        elif action == 'add_coins':
            conn.execute('UPDATE users SET coins = coins + 5000 WHERE telegram_id = ?', (target_id,))
        conn.commit()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
