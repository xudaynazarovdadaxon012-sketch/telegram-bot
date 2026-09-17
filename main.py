import os
import threading
import sqlite3
import telebot
from flask import Flask, render_template, request, jsonify

# Render Environment Variable'dan token olinadi
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# --- DATABASE OPTIMIZATION ---
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('miniapp.html')

@app.route('/get_user', methods=['GET'])
def get_user():
    tg_id = request.args.get('tg_id')
    if not tg_id:
        return jsonify({'error': 'Telegram ID topilmadi'}), 400

    tg_id = str(tg_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT score, energy FROM users WHERE telegram_id = ?', (tg_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute('INSERT INTO users (telegram_id, score, energy) VALUES (?, 0, 1000)', (tg_id,))
        conn.commit()
        score, energy = 0, 1000
    else:
        score, energy = row['score'], row['energy']
        
    conn.close()
    return jsonify({'score': score, 'energy': energy})

@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id')
    score = data.get('score')
    energy = data.get('energy')

    if not tg_id or score is None or energy is None:
        return jsonify({'error': 'Noto\'g\'ri ma\'lumotlar'}), 400

    tg_id = str(tg_id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_id, score, energy, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(telegram_id) DO UPDATE SET score = ?, energy = ?, updated_at = CURRENT_TIMESTAMP
        ''', (tg_id, score, energy, score, energy))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- BOT HANDLERS ---
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Render domeniz avtomatik aniqlanadi yoki havola shakllantiriladi
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegram-bot-7n6t.onrender.com')
        
        web_app = telebot.types.WebAppInfo(url=render_url)
        markup.add(telebot.types.InlineKeyboardButton("🚀 Play Mini App", web_app=web_app))
        bot.reply_to(message, "Hush kelibsiz! O'yinni boshlash uchun pastdagi tugmani bosing:", reply_markup=markup)

def run_bot():
    if bot:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Botda xatolik: {e}")

if __name__ == '__main__':
    if bot:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
