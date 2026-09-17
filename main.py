import os
import threading
import sqlite3
import telebot
from flask import Flask, request, jsonify, render_template_string

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

# --- BAZA OPTIMIZATSIYASI ---
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

# --- PAPKASIZ HTML O'QISH ---
@app.route('/')
def index():
    # miniapp.html faylini hech qanday 'templates' papkasisiz to'g'ridan-to'g'ri o'qiydi
    with open('miniapp.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

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

# --- BOT ---
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = telebot.types.InlineKeyboardMarkup()
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://sizning-saytingiz.onrender.com')
        web_app = telebot.types.WebAppInfo(url=render_url)
        markup.add(telebot.types.InlineKeyboardButton("🚀 Play Mini App", web_app=web_app))
        bot.reply_to(message, "Hush kelibsiz! O'yinni boshlash uchun pastdagi tugmani bosing:", reply_markup=markup)

# --- BOT THREADING & SERVER RUN ---
def run_bot():
    if bot:
        print("Bot ishga tushdi...")
        try:
            bot.remove_webhook()  # Eski webhook'larni tozalaydi
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Botda xatolik: {e}")

if __name__ == '__main__':
    # Baza jadvallarini yaratish
    init_db()
    
    # Botni alohida treda ishga tushirish
    if bot:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()

    # Flask serverini ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
