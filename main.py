import os
import time
import sqlite3
import threading
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
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
                is_banned INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                reward INTEGER,
                link TEXT
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('miniapp.html')

# --- USER APIs ---
@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get('user_id')
    username = data.get('username', 'User')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'No user_id'}), 400

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user:
            conn.execute(
                'INSERT INTO users (telegram_id, username, coins, energy) VALUES (?, ?, ?, ?)',
                (user_id, username, 0, 1000)
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        
        return jsonify({
            'status': 'success',
            'data': dict(user),
            'is_admin': user_id in ADMIN_IDS
        })

@app.route('/api/tap', methods=['POST'])
def handle_tap():
    data = request.json or {}
    user_id = data.get('user_id')
    count = data.get('count', 1)

    if count > 20: # Anti-cheat
        return jsonify({'status': 'error', 'message': 'Cheat detected'}), 400

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        if not user or user['is_banned']:
            return jsonify({'status': 'error', 'message': 'Banned or invalid'}), 403

        earned = count * user['tap_level']
        new_coins = user['coins'] + earned
        new_energy = max(0, user['energy'] - count)

        conn.execute(
            'UPDATE users SET coins = ?, energy = ? WHERE telegram_id = ?',
            (new_coins, new_energy, user_id)
        )
        conn.commit()
        return jsonify({'status': 'success', 'coins': new_coins, 'energy': new_energy})

# --- ADMIN PANEL APIs ---
@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    data = request.json or {}
    admin_id = data.get('admin_id')
    if admin_id not in ADMIN_IDS:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    with get_db() as conn:
        total_users = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        total_coins = conn.execute('SELECT SUM(coins) as s FROM users').fetchone()['s'] or 0
        banned_users = conn.execute('SELECT COUNT(*) as c FROM users WHERE is_banned = 1').fetchone()['c']
        users_list = [dict(row) for row in conn.execute('SELECT * FROM users ORDER BY coins DESC LIMIT 20').fetchall()]

    return jsonify({
        'status': 'success',
        'stats': {
            'total_users': total_users,
            'total_coins': total_coins,
            'banned_users': banned_users
        },
        'users': users_list
    })

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json or {}
    admin_id = data.get('admin_id')
    action = data.get('action') # 'ban', 'add_coins'
    target_id = data.get('target_id')

    if admin_id not in ADMIN_IDS:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    with get_db() as conn:
        if action == 'ban':
            conn.execute('UPDATE users SET is_banned = 1 WHERE telegram_id = ?', (target_id,))
        elif action == 'unban':
            conn.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (target_id,))
        elif action == 'add_coins':
            amount = data.get('amount', 10000)
            conn.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?', (amount, target_id))
        conn.commit()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
