import os
import time
import sqlite3
from flask import Flask, request, jsonify, render_template
import telebot
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
WEBAPP_URL = os.getenv("https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATO: BOT_TOKEN Render Environment Variables'da topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__, template_folder='.', static_folder='.')

# ==========================================
# WEBHOOK ENDPOINT (409 CONFLICT HAL QILISH)
# ==========================================
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return jsonify({"status": "error"}), 400

# WEBHOOK O'RNATISH
def setup_webhook():
    if WEBAPP_URL:
        webhook_url = f"{WEBAPP_URL.rstrip('/')}/{BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)

# Application startup'da webhookni bir marta o'rnatamiz
try:
    setup_webhook()
except Exception as e:
    print(f"Webhook o'rnatishda xato: {e}")

# ==========================================
# DATABASE SOZLAMALARI
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
# ROUTES & HANDLERS
# ==========================================
@app.route('/')
def index():
    return render_template('miniapp.html')

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup()
    if WEBAPP_URL:
        keyboard.add(InlineKeyboardButton(text="🚀 O'yinni Boshlash", web_app=telebot.types.WebAppInfo(url=WEBAPP_URL)))
    
    bot.send_message(
        message.chat.id,
        "🪙 **Clicker Pro Game'ga xush kelibsiz!**\n\nO'yinni boshlash uchun tugmani bosing:",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
