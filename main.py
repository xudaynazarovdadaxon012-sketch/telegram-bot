import os
import random
import threading
import sqlite3
import telebot
from flask import Flask, request, jsonify, render_template_string

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db', timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 1000,
            tap_level INTEGER DEFAULT 1,
            max_energy INTEGER DEFAULT 1000,
            referrals INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    with open('miniapp.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/get_user', methods=['GET'])
def get_user():
    tg_id = request.args.get('tg_id', 'demo_user')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (tg_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute('INSERT INTO users (telegram_id, score, energy, tap_level, max_energy, referrals) VALUES (?, 500, 1000, 1, 1000, 0)', (tg_id,))
        conn.commit()
        data = {'score': 500, 'energy': 1000, 'tap_level': 1, 'max_energy': 1000, 'referrals': 0}
    else:
        data = dict(row)
        
    conn.close()
    return jsonify(data)

@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id', 'demo_user')
    score = data.get('score')
    energy = data.get('energy')
    tap_level = data.get('tap_level', 1)
    max_energy = data.get('max_energy', 1000)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET score = ?, energy = ?, tap_level = ?, max_energy = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    ''', (score, energy, tap_level, max_energy, tg_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/open_case', methods=['POST'])
def open_case():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id', 'demo_user')
    case_price = 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT score FROM users WHERE telegram_id = ?', (tg_id,))
    row = cursor.fetchone()

    if not row or row['score'] < case_price:
        conn.close()
        return jsonify({'error': 'Mablag\' yetarli emas!'}), 400

    # CS Style Drop Logikasi
    prizes = [50, 100, 150, 300, 500, 1000, 2500]
    weights = [40, 30, 15, 9, 4, 1.8, 0.2]
    win_amount = random.choices(prizes, weights=weights)[0]

    new_score = row['score'] - case_price + win_amount
    cursor.execute('UPDATE users SET score = ? WHERE telegram_id = ?', (new_score, tg_id))
    conn.commit()
    conn.close()

    return jsonify({'win': win_amount, 'new_score': new_score})

if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = telebot.types.InlineKeyboardMarkup()
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        web_app = telebot.types.WebAppInfo(url=render_url)
        markup.add(telebot.types.InlineKeyboardButton("🎮 Play & Open Cases", web_app=web_app))
        bot.reply_to(message, "🔥 Premium Mini App'ga xush kelibsiz!", reply_markup=markup)

def run_bot():
    if bot:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Bot error: {e}")

if __name__ == '__main__':
    if bot:
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
