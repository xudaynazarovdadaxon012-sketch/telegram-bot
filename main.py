import os
import hmac
import hashlib
import time
import sqlite3
import threading
from urllib.parse import parse_qsl
from flask import Flask, request, jsonify, render_template
import telebot
from telebot.types import LabeledPrice

# ==========================================
# 1. RENDER ENVIRONMENT VARIABLES & CONFIG
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
WEBAPP_URL = os.getenv("https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATO: BOT_TOKEN Render Environment Variables'da topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__, template_folder='.', static_folder='.')

# ==========================================
# 2. DATABASE (SQLite) SOZLAMALARI
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
            last_energy_update INTEGER,
            referred_by INTEGER,
            created_at INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def update_user_energy(user_id):
    """Energiya vaqt o'tishi bilan o'zi tiklanishi uchun"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT energy, last_energy_update FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        current_energy = row['energy']
        last_update = row['last_energy_update'] or int(time.time())
        now = int(time.time())
        
        # Har 3 soniyada 1 energiya tiklanadi (maksimum 100)
        passed_seconds = now - last_update
        recovered_energy = passed_seconds // 3
        
        if recovered_energy > 0 and current_energy < 100:
            new_energy = min(100, current_energy + recovered_energy)
            cursor.execute("UPDATE users SET energy = ?, last_energy_update = ? WHERE user_id = ?",
                           (new_energy, now, user_id))
            conn.commit()
            conn.close()
            return new_energy
    conn.close()
    return row['energy'] if row else 100

# ==========================================
# 4. GAME API (CLICKER, BALANCE, REFERRAL)
# ==========================================
@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "User ID yetishmayapti"}), 400

    energy = update_user_energy(user_id)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        now = int(time.time())
        cursor.execute("INSERT INTO users (user_id, coins, energy, last_energy_update, created_at) VALUES (?, ?, ?, ?, ?)",
                       (user_id, 0, 100, now, now))
        conn.commit()
        coins, energy = 0, 100
    else:
        coins, energy = row['coins'], row['energy']

    conn.close()
    return jsonify({"status": "success", "coins": coins, "energy": energy})

@app.route('/api/user/tap', methods=['POST'])
def tap_coin():
    data = request.json or {}
    user_id = data.get("user_id")
    count = data.get("count", 1)

    if not user_id:
        return jsonify({"status": "error", "message": "User ID yetishmayapti"}), 400

    energy = update_user_energy(user_id)

    if energy < count:
        return jsonify({"status": "error", "message": "Energiya yetarli emas!"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ?, energy = energy - ?, last_energy_update = ? WHERE user_id = ?",
                   (count, count, int(time.time()), user_id))
    conn.commit()
    
    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    return jsonify({"status": "success", "coins": row['coins'], "energy": row['energy']})

# ==========================================
# 5. MONETIZATION (TELEGRAM STARS IAP)
# ==========================================
@app.route('/api/buy-stars-item', methods=['POST'])
def buy_stars_item():
    data = request.json or {}
    user_id = data.get("user_id")
    item_type = data.get("item_type")
    
    prices = {
        'chest_gold': {'title': 'Oltin Quti (Lootbox)', 'price': 50},
        'energy_full': {'title': 'To\'liq Energiya', 'price': 25},
        'coins_pack': {'title': '10,000 Tangalar', 'price': 100}
    }
    
    if item_type not in prices:
        return jsonify({"status": "error", "message": "Noma'lum mahsulot"}), 400

    item = prices[item_type]
    
    try:
        invoice_link = bot.create_invoice_link(
            title=item['title'],
            description=f"Clicker Gold: {item['title']}",
            payload=f"payload_{user_id}_{item_type}_{int(time.time())}",
            provider_token="", 
            currency="XTR",    
            prices=[LabeledPrice(label=item['title'], amount=item['price'])]
        )
        return jsonify({"status": "success", "invoice_link": invoice_link})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 6. MAIN INDEX ROUTE
# ==========================================
@app.route('/')
def index():
    return render_template('miniapp.html')

# ==========================================
# 7. TELEGRAM BOT HANDLERS & COMMANDS
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        now = int(time.time())
        cursor.execute("INSERT INTO users (user_id, coins, energy, last_energy_update, referred_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, 100, 100, now, referred_by, now))
        
        # Referal uchun bonus berish
        if referred_by:
            cursor.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (referred_by,))
            try:
                bot.send_message(referred_by, "🎉 **Yangi do'st taklif qildingiz!**\nSizga +500 tanga taqdim etildi!")
            except Exception:
                pass
        conn.commit()
    conn.close()

    keyboard = telebot.types.InlineKeyboardMarkup()
    if WEBAPP_URL:
        web_app_info = telebot.types.WebAppInfo(url=WEBAPP_URL)
        keyboard.add(telebot.types.InlineKeyboardButton(text="🎮 O'yinni Boshlash", web_app=web_app_info))
    
    bot.send_message(
        message.chat.id,
        "🪙 **Clicker Gold o'yiniga xush kelibsiz!**\n\n"
        "Tangalar yig'ing, energiyangizni oshiring va Telegram Stars yutib oling!\n\n"
        "👇 O'yinni boshlash uchun quyidagi tugmani bosing:",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.from_user.id
    
    if ADMIN_ID == 0 or user_id != ADMIN_ID:
        bot.reply_to(message, "⛔️ Siz admin emassiz yoki ADMIN_ID kiritilmagan!")
        return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(coins) FROM users")
    total_coins = cursor.fetchone()[0] or 0
    conn.close()

    admin_text = (
        "📊 **ADMIN DASHBOARD**\n\n"
        f"👥 **Jami foydalanuvchilar:** `{total_users}` ta\n"
        f"🪙 **Jami bosilgan tangalar:** `{total_coins}`\n"
        f"💳 **Monetizatsiya:** Telegram Stars (Active)\n"
        f"🛡 **Xavfsizlik:** Active"
    )
    bot.send_message(message.chat.id, admin_text)

# Telegram Stars orqali to'lov muvaffaqiyatli amalga oshganda
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    
    conn = get_db()
    cursor = conn.cursor()
    
    if "energy_full" in payload:
        cursor.execute("UPDATE users SET energy = 100 WHERE user_id = ?", (user_id,))
        bot.send_message(message.chat.id, "⚡️ Energiyangiz to'liq tiklandi!")
    elif "coins_pack" in payload:
        cursor.execute("UPDATE users SET coins = coins + 10000 WHERE user_id = ?", (user_id,))
        bot.send_message(message.chat.id, "🪙 Hisobingizga +10,000 tanga qo'shildi!")
    
    conn.commit()
    conn.close()

# ==========================================
# 8. BACKGROUND BOT THREAD (LONG POLLING HAL QILISH)
# ==========================================
def start_bot_polling():
    try:
        bot.remove_webhook()
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot Polling Xato: {e}")

# Botni alohida fonda (Thread) xatosiz berish
threading.Thread(target=start_bot_polling, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
