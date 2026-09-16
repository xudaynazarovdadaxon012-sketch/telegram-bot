import os
import time
import sqlite3
from flask import Flask, request, jsonify, render_template
import telebot
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# 1. CONFIG & TELEBOT INITIALIZATION
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
WEBAPP_URL = os.getenv("https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATO: BOT_TOKEN Render Environment Variables'da topilmadi!")

# Render uchun thread'ni o'chiramiz (threaded=False)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown", threaded=False)
app = Flask(__name__, template_folder='.', static_folder='.')

# ==========================================
# 2. WEBHOOK SETUP (409 CONFLICT HAL QILISH)
# ==========================================
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return jsonify({"status": "forbidden"}), 403

# Auto Webhook initialisation
if WEBAPP_URL:
    clean_url = WEBAPP_URL.rstrip('/')
    webhook_url = f"{clean_url}/{BOT_TOKEN}"
    try:
        bot.remove_webhook()
        time.sleep(0.5)
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook muvaffaqiyatli o'rnatildi: {webhook_url}")
    except Exception as e:
        print(f"❌ Webhook o'rnatishda xato: {e}")

# ==========================================
# 3. DATABASE (SQLite) SOZLAMALARI
# ==========================================
DB_FILE = "game_database.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100,
            max_energy INTEGER DEFAULT 100,
            tap_power INTEGER DEFAULT 1,
            profit_per_hour INTEGER DEFAULT 0,
            last_login_time INTEGER,
            last_energy_update INTEGER,
            daily_streak INTEGER DEFAULT 0,
            last_claim_day INTEGER DEFAULT 0,
            referred_by INTEGER,
            created_at INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT,
            level INTEGER DEFAULT 1,
            UNIQUE(user_id, card_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 4. GAME API ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('miniapp.html')

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "User ID yetishmayapti"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        now = int(time.time())
        cursor.execute("""
            INSERT INTO users (user_id, coins, energy, max_energy, tap_power, profit_per_hour, last_login_time, last_energy_update, created_at)
            VALUES (?, 100, 100, 100, 1, 0, ?, ?, ?)
        """, (user_id, now, now, now))
        conn.commit()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = dict(cursor.fetchone())
    conn.close()

    return jsonify({"status": "success", "user": user})

# ==========================================
# 5. TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        now = int(time.time())
        cursor.execute("""
            INSERT INTO users (user_id, coins, energy, max_energy, tap_power, profit_per_hour, last_login_time, last_energy_update, created_at)
            VALUES (?, 100, 100, 100, 1, 0, ?, ?, ?)
        """, (user_id, now, now, now))
        conn.commit()
    conn.close()

    keyboard = InlineKeyboardMarkup()
    if WEBAPP_URL:
        keyboard.add(InlineKeyboardButton(text="🚀 O'yinni Boshlash", web_app=telebot.types.WebAppInfo(url=WEBAPP_URL)))
    
    bot.send_message(
        message.chat.id,
        "🪙 **Clicker Pro Game'ga xush kelibsiz!**\n\n"
        "Tangalar yig'ing, soatlik pasiv daromadingizni oshiring va do'stlaringizni taklif qiling!\n\n"
        "O'yinni boshlash uchun quyidagi tugmani bosing:",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
