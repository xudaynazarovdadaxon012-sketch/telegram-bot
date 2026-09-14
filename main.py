import os
import time
import sqlite3
import threading
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8898979946] # O'zingizning Telegram ID'ingiz

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
                last_active INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

init_db()

# --- TELEGRAM BOT POLLING ---
def run_bot_polling():
    if not BOT_TOKEN: return
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass

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

                    if text.startswith("/start"):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": chat_id,
                            "text": f"⚡ **Cyber Pro Hub Mini App**ga xush kelibsiz!\n\nPastdagi tugma orqali o'yinga kiring:",
                            "parse_mode": "Markdown",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [{"text": "🚀 Mini App'ni Ochish", "web_app": {"url": "https://telegram-bot-7n6t.onrender.com"}}]
                                ]
                            }
                        }
                        requests.post(send_url, json=payload)
        except: time.sleep(3)

threading.Thread(target=run_bot_polling, daemon=True).start()

# --- ROUTES & APIs ---
@app.route('/')
def index():
    return render_template('miniapp.html')

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get('user_id')
    username = data.get('username', 'User')

    if not user_id:
        return jsonify({'status': 'error'}), 400

    now = int(time.time())
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user:
            conn.execute(
                'INSERT INTO users (telegram_id, username, coins, energy, last_active) VALUES (?, ?, ?, ?, ?)',
                (user_id, username, 0, 1000, now)
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()

        offline_time = now - user['last_active']
        passive_coins = 0
        if user['autotap_level'] > 0 and offline_time > 60:
            passive_coins = min(offline_time * user['autotap_level'], 50000)
            conn.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?', (passive_coins, user_id))

        conn.execute('UPDATE users SET last_active = ? WHERE telegram_id = ?', (now, user_id))
        conn.commit()

        return jsonify({
            'status': 'success',
            'data': dict(user),
            'passive_coins': passive_coins,
            'is_admin': user_id in ADMIN_IDS
        })

@app.route('/api/tap', methods=['POST'])
def handle_tap():
    data = request.json or {}
    user_id = data.get('user_id')
    count = data.get('count', 1)

    if count > 20: return jsonify({'error': 'Cheat detected'}), 400

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user or user['is_banned']: return jsonify({'error': 'Denied'}), 403

        earned = count * user['tap_level']
        conn.execute(
            'UPDATE users SET coins = coins + ?, energy = max(0, energy - ?) WHERE telegram_id = ?',
            (earned, count, user_id)
        )
        conn.commit()
        return jsonify({'status': 'success'})

@app.route('/api/boost/buy', methods=['POST'])
def buy_boost():
    data = request.json or {}
    user_id = data.get('user_id')
    boost_type = data.get('type')

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if boost_type == 'multitap' and user['coins'] >= 1000:
            conn.execute('UPDATE users SET coins = coins - 1000, tap_level = tap_level + 1 WHERE telegram_id = ?', (user_id,))
        elif boost_type == 'energy' and user['coins'] >= 1500:
            conn.execute('UPDATE users SET coins = coins - 1500, max_energy = max_energy + 500, energy = energy + 500 WHERE telegram_id = ?', (user_id,))
        else:
            return jsonify({'error': 'Mablag\' yetarli emas'}), 400
        conn.commit()
        return jsonify({'status': 'success'})

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    data = request.json or {}
    if data.get('admin_id') not in ADMIN_IDS: return jsonify({'error': 'Unauthorized'}), 403

    with get_db() as conn:
        users = [dict(r) for r in conn.execute('SELECT * FROM users ORDER BY coins DESC LIMIT 30').fetchall()]
        total_u = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        total_c = conn.execute('SELECT SUM(coins) as s FROM users').fetchone()['s'] or 0

    return jsonify({'status': 'success', 'stats': {'total_users': total_u, 'total_coins': total_c}, 'users': users})

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json or {}
    if data.get('admin_id') not in ADMIN_IDS: return jsonify({'error': 'Unauthorized'}), 403

    action = data.get('action')
    target_id = data.get('target_id')
    with get_db() as conn:
        if action == 'ban':
            conn.execute('UPDATE users SET is_banned = 1 WHERE telegram_id = ?', (target_id,))
        elif action == 'unban':
            conn.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (target_id,))
        elif action == 'add_coins':
            conn.execute('UPDATE users SET coins = coins + 50000 WHERE telegram_id = ?', (target_id,))
        conn.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
