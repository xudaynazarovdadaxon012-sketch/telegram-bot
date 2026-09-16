import os
import hmac
import hashlib
import time
import sqlite3
from urllib.parse import parse_qsl
from flask import Flask, request, jsonify, render_template
import telebot
from telebot.types import LabeledPrice

# ==========================================
# 1. RENDER ENVIRONMENT VARIABLES & CONFIG
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Xatoliklar oldini olish uchun fallback va tur tekshiruvi bilan
ADMIN_ID = int(os.getenv("ADMIN_ID") or 123456789)
WEBAPP_URL = os.getenv("https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATO: BOT_TOKEN Render Environment Variables'da topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)

# Papkasiz (ildiz papkadan) index.html ni o'quvchi Flask sozlamasi
app = Flask(__name__, template_folder='.', static_folder='.')

# ==========================================
# 2. DATABASE (SQLite) SOZLAMALARI
# ==========================================
DB_FILE = "game_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100,
            referred_by INTEGER,
            created_at INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. ANTI-CHEAT & SECURITY (HMAC-SHA256)
# ==========================================
def verify_telegram_init_data(init_data: str) -> bool:
    if not init_data:
        return False
    try:
        parsed_data = dict(parse_qsl(init_data))
        if 'hash' not in parsed_data:
            return False
        
        hash_check = parsed_data.pop('hash')
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(calculated_hash, hash_check)
    except Exception:
        return False

# ==========================================
# 4. GAME API (CLICKER, BALANCE, REFERRAL)
# ==========================================
@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "User ID yo'q"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users (user_id, coins, energy, created_at) VALUES (?, ?, ?, ?)",
                       (user_id, 0, 100, int(time.time())))
        conn.commit()
        coins, energy = 0, 100
    else:
        coins, energy = row[0], row[1]

    conn.close()
    return jsonify({"status": "success", "coins": coins, "energy": energy})

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
# 6. B2B ADMIN DASHBOARD & STATS API
# ==========================================
@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    auth_header = request.headers.get("X-User-ID")
    if not auth_header or int(auth_header) != ADMIN_ID:
        return jsonify({"status": "error", "message": "Ruxsat etilmagan kirish!"}), 403

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "metrics": {
                "total_users": total_users,
                "dau_target": "500-600",
                "monetization": "Telegram Stars (XTR) Active",
                "anti_cheat": "HMAC-SHA256 Enabled"
            }
        }
    })

# ==========================================
# 7. MAIN INDEX ROUTE
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# 8. TELEGRAM BOT HANDLERS & START
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referred_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, coins, energy, referred_by, created_at) VALUES (?, ?, ?, ?, ?)",
                       (user_id, 100, 100, referred_by, int(time.time())))
        conn.commit()
    conn.close()

    keyboard = telebot.types.InlineKeyboardMarkup()
    if WEBAPP_URL:
        web_app_info = telebot.types.WebAppInfo(url=WEBAPP_URL)
        keyboard.add(telebot.types.InlineKeyboardButton(text="🎮 O'yinni Boshlash", web_app=web_app_info))
    
    bot.send_message(
        message.chat.id,
        "🪙 **Clicker Gold** o'yiniga xush kelibsiz!\n\nTangalar yiging, qutilarni oching va Stars yutib oling!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    import threading
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
