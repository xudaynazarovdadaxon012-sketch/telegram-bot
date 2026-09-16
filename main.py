import os
import time
import random
import sqlite3
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("https://telegram-bot-7n6t.onrender.com")

if not BOT_TOKEN:
    raise ValueError("XATO: BOT_TOKEN kiritilmagan!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown", threaded=False)
app = Flask(__name__)

DB_FILE = "game_database.db"

# --- HTML KODI (PAPKASIZ, TO'G'RIDAN-TO'G'RI KOD ICHIDA) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Clicker Pro</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0f172a; --card: rgba(30, 41, 59, 0.9); --accent: #fbbf24; --text: #ffffff; --muted: #94a3b8; }
        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; font-family: 'Fredoka', sans-serif; }
        body { background: radial-gradient(circle at top, #1e293b 0%, var(--bg) 100%); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        .header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--card); border-bottom: 1px solid rgba(255,255,255,0.05); }
        .balance-group { display: flex; gap: 15px; font-weight: 700; font-size: 16px; }
        .tab-content { flex: 1; display: none; padding: 15px; overflow-y: auto; }
        .tab-content.active { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; gap: 15px; }
        .hamster-btn { width: 190px; height: 190px; border-radius: 50%; background: radial-gradient(circle, #f59e0b 0%, #b45309 100%); box-shadow: 0 10px 30px rgba(245, 158, 11, 0.4); display: flex; align-items: center; justify-content: center; font-size: 90px; cursor: pointer; transition: transform 0.05s; margin-top: 20px; }
        .hamster-btn:active { transform: scale(0.92); }
        .floating-text { position: absolute; font-size: 30px; font-weight: 700; color: #fff; pointer-events: none; animation: floatUp 0.6s ease-out forwards; }
        @keyframes floatUp { 0% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(-70px); } }
        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; width: 100%; }
        .item-card { background: var(--card); border-radius: 12px; padding: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.05); width: 100%; }
        .btn-action { background: #2563eb; color: white; border: none; padding: 10px 12px; border-radius: 8px; font-weight: 700; margin-top: 8px; cursor: pointer; width: 100%; }
        .leaderboard-list { width: 100%; display: flex; flex-direction: column; gap: 8px; }
        .leader-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: var(--card); border-radius: 10px; font-size: 14px; }
        .nav-bar { background: #0f172a; display: flex; padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.05); }
        .nav-link { flex: 1; text-align: center; color: var(--muted); font-size: 11px; cursor: pointer; }
        .nav-link.active { color: var(--accent); }
        .nav-icon { font-size: 18px; display: block; }
    </style>
</head>
<body>
    <div class="header">
        <div class="balance-group">
            <span>🪙 <span id="coins">0</span></span>
            <span>⭐️ <span id="stars">0</span></span>
        </div>
    </div>

    <!-- TAB 1: TAPPER -->
    <div id="tabTap" class="tab-content active">
        <div class="hamster-btn" id="hamsterBtn">🐹</div>
        <div style="width: 100%; max-width: 280px; margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                <span>⚡️ Energiya</span>
                <span id="energyText">1000 / 1000</span>
            </div>
            <div style="width: 100%; height: 10px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
                <div id="energyFill" style="width: 100%; height: 100%; background: var(--accent);"></div>
            </div>
        </div>
    </div>

    <!-- TAB 2: DAILY PASS -->
    <div id="tabDaily" class="tab-content">
        <h3>📅 Daily Pass</h3>
        <div class="item-card">
            <h4>⚡️ Daily Streak Pass</h4>
            <p style="font-size: 12px; color: var(--muted); margin: 6px 0;">5 Stars evaziga sotib oling va har kuni doimiy o'sib boruvchi bonus tangalar oling!</p>
            <div id="passStatus" style="font-weight: bold; color: var(--accent); margin: 8px 0;">Status: Yo'q</div>
            <button class="btn-action" id="btnBuyPass" style="background: #eab308;" onclick="buyPass()">5 Stars ga Sotib Olish</button>
            <button class="btn-action" id="btnClaimDaily" style="background: #10b981; display: none;" onclick="claimDaily()">Kunlik Bonusni Olish 🎁</button>
        </div>
    </div>

    <!-- TAB 3: CASES -->
    <div id="tabCases" class="tab-content">
        <h3>📦 CS Style Qutilar</h3>
        <div class="grid-container">
            <div class="item-card">
                <h4>📦 Oddiy Quti</h4>
                <button class="btn-action" onclick="openCase('coin_1k')">1,000 🪙</button>
            </div>
            <div class="item-card">
                <h4>📦 O'rta Quti</h4>
                <button class="btn-action" onclick="openCase('coin_5k')">5,000 🪙</button>
            </div>
            <div class="item-card">
                <h4>⭐ Bronze Stars</h4>
                <button class="btn-action" style="background: #eab308;" onclick="openCase('stars_5')">5 ⭐️</button>
            </div>
            <div class="item-card">
                <h4>⭐ Gold Stars</h4>
                <button class="btn-action" style="background: #eab308;" onclick="openCase('stars_20')">20 ⭐️</button>
            </div>
        </div>
    </div>

    <!-- TAB 4: SPIN -->
    <div id="tabSpin" class="tab-content">
        <h3>🎰 Wheel of Fortune</h3>
        <div class="grid-container">
            <div class="item-card">
                <h4>🪙 Tanga Spin</h4>
                <button class="btn-action" onclick="spin('coin_500')">500 🪙</button>
            </div>
            <div class="item-card">
                <h4>⭐️ Stars Spin</h4>
                <button class="btn-action" style="background: #eab308;" onclick="spin('stars_2')">2 ⭐️</button>
            </div>
        </div>
    </div>

    <!-- TAB 5: LEADERBOARD -->
    <div id="tabTop" class="tab-content">
        <h3>🏆 Peshqadamlar Ro'yxati</h3>
        <div class="leaderboard-list" id="leaderboardList">
            <div style="text-align: center; color: var(--muted);">Yuklanmoqda...</div>
        </div>
    </div>

    <div class="nav-bar">
        <div class="nav-link active" onclick="switchTab('tabTap', this)"><span class="nav-icon">🪙</span>Tap</div>
        <div class="nav-link" onclick="switchTab('tabDaily', this)"><span class="nav-icon">📅</span>Pass</div>
        <div class="nav-link" onclick="switchTab('tabCases', this)"><span class="nav-icon">📦</span>Qutilar</div>
        <div class="nav-link" onclick="switchTab('tabSpin', this)"><span class="nav-icon">🎰</span>Spin</div>
        <div class="nav-link" onclick="switchTab('tabTop', this)"><span class="nav-icon">🏆</span>TOP</div>
    </div>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) tg.expand();

        const userId = tg?.initDataUnsafe?.user?.id || 12345678;
        const username = tg?.initDataUnsafe?.user?.username || tg?.initDataUnsafe?.user?.first_name || "Player";

        let coins = 0, stars = 0, energy = 1000, maxEnergy = 1000, tapPower = 1;

        async function sync() {
            const res = await fetch('/api/user/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username: username })
            });
            const data = await res.json();
            if (data.status === 'success') {
                coins = data.user.coins;
                stars = data.user.stars;
                energy = data.user.energy;
                maxEnergy = data.user.max_energy;
                tapPower = data.user.tap_power;

                if (data.user.has_daily_pass === 1) {
                    document.getElementById('passStatus').innerText = `Aktiv (Streak: ${data.user.daily_streak} kun)`;
                    document.getElementById('btnBuyPass').style.display = 'none';
                    document.getElementById('btnClaimDaily').style.display = 'block';
                }
                updateUI();
            }
        }

        function updateUI() {
            document.getElementById('coins').innerText = coins.toLocaleString();
            document.getElementById('stars').innerText = stars;
            document.getElementById('energyText').innerText = `${energy} / ${maxEnergy}`;
            document.getElementById('energyFill').style.width = `${(energy / maxEnergy) * 100}%`;
        }

        document.getElementById('hamsterBtn').addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (energy < tapPower) return;
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

            const touch = e.touches[0];
            showText(touch.clientX, touch.clientY, `+${tapPower}`);

            coins += tapPower;
            energy -= tapPower;
            updateUI();

            fetch('/api/user/tap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, count: 1 })
            });
        });

        function showText(x, y, text) {
            const el = document.createElement('div');
            el.className = 'floating-text';
            el.innerText = text;
            el.style.left = `${x - 15}px`;
            el.style.top = `${y - 30}px`;
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 600);
        }

        function switchTab(id, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            el.classList.add('active');

            if (id === 'tabTop') loadLeaderboard();
        }

        async function buyPass() {
            const res = await fetch('/api/user/buy_pass', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            const data = await res.json();
            if (data.status === 'success') {
                stars = data.stars;
                document.getElementById('passStatus').innerText = "Aktiv (Streak: 0 kun)";
                document.getElementById('btnBuyPass').style.display = 'none';
                document.getElementById('btnClaimDaily').style.display = 'block';
                updateUI();
                alert("Daily Pass muvaffaqiyatli sotib olindi!");
            } else alert(data.message);
        }

        async function claimDaily() {
            const res = await fetch('/api/user/claim_daily', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            const data = await res.json();
            if (data.status === 'success') {
                coins = data.coins;
                document.getElementById('passStatus').innerText = `Aktiv (Streak: ${data.daily_streak} kun)`;
                updateUI();
                alert(`Kunlik bonus olindi: +${data.reward} 🪙`);
            } else alert(data.message);
        }

        async function loadLeaderboard() {
            const res = await fetch('/api/leaderboard');
            const data = await res.json();
            if (data.status === 'success') {
                const list = document.getElementById('leaderboardList');
                list.innerHTML = '';
                data.leaderboard.forEach((item, index) => {
                    const row = document.createElement('div');
                    row.className = 'leader-item';
                    row.innerHTML = `<span>#${index + 1} ${item.username}</span> <span>⭐️ ${item.stars} | 🪙 ${item.coins.toLocaleString()}</span>`;
                    list.appendChild(row);
                });
            }
        }

        async function openCase(type) {
            const res = await fetch('/api/game/open_case', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, case_type: type })
            });
            const data = await res.json();
            if (data.status === 'success') {
                coins = data.coins;
                stars = data.stars;
                updateUI();
                alert(`Yutuq: ${data.win_amount} ${data.win_type}`);
            } else alert(data.message);
        }

        async function spin(type) {
            const res = await fetch('/api/game/spin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, spin_type: type })
            });
            const data = await res.json();
            if (data.status === 'success') {
                coins = data.coins;
                stars = data.stars;
                updateUI();
                alert(`Natija: ${data.win_amount} ${data.win_type}`);
            } else alert(data.message);
        }

        sync();
    </script>
</body>
</html>
"""

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
            username TEXT DEFAULT 'Player',
            coins INTEGER DEFAULT 1000,
            stars INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 1000,
            max_energy INTEGER DEFAULT 1000,
            tap_power INTEGER DEFAULT 1,
            profit_per_hour INTEGER DEFAULT 0,
            level TEXT DEFAULT 'Bronze',
            has_daily_pass INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim INTEGER DEFAULT 0,
            last_energy_update INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return jsonify({"status": "forbidden"}), 403

if WEBAPP_URL:
    clean_url = WEBAPP_URL.rstrip('/')
    try:
        bot.remove_webhook()
        time.sleep(0.3)
        bot.set_webhook(url=f"{clean_url}/{BOT_TOKEN}")
    except Exception as e:
        print(f"Webhook error: {e}")

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.json or {}
    user_id = data.get("user_id")
    username = data.get("username", "Player")

    if not user_id:
        return jsonify({"status": "error"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    now = int(time.time())
    if not user:
        cursor.execute("""
            INSERT INTO users (user_id, username, coins, stars, energy, max_energy, tap_power, profit_per_hour, level, has_daily_pass, daily_streak, last_daily_claim, last_energy_update)
            VALUES (?, ?, 1000, 0, 1000, 1000, 1, 0, 'Bronze', 0, 0, 0, ?)
        """, (user_id, username, now))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()

    user_data = dict(user)
    conn.close()
    return jsonify({"status": "success", "user": user_data})

@app.route('/api/user/tap', methods=['POST'])
def handle_tap():
    data = request.json or {}
    user_id = data.get("user_id")
    count = data.get("count", 1)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT coins, energy, tap_power FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error"}), 404

    earned = count * user['tap_power']
    new_coins = user['coins'] + earned
    new_energy = max(0, user['energy'] - earned)

    cursor.execute("UPDATE users SET coins = ?, energy = ? WHERE user_id = ?", (new_coins, new_energy, user_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "coins": new_coins, "energy": new_energy})

@app.route('/api/user/buy_pass', methods=['POST'])
def buy_pass():
    data = request.json or {}
    user_id = data.get("user_id")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT stars, has_daily_pass FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "Foydalanuvchi topilmadi"}), 404

    if user['has_daily_pass'] == 1:
        conn.close()
        return jsonify({"status": "error", "message": "Sizda tayyor Daily Pass bor!"}), 400

    if user['stars'] < 5:
        conn.close()
        return jsonify({"status": "error", "message": "Stars yetarli emas! (5 Stars kerak)"}), 400

    cursor.execute("UPDATE users SET stars = stars - 5, has_daily_pass = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    cursor.execute("SELECT coins, stars, has_daily_pass FROM users WHERE user_id = ?", (user_id,))
    updated = cursor.fetchone()
    conn.close()

    return jsonify({"status": "success", "stars": updated['stars'], "has_daily_pass": updated['has_daily_pass']})

@app.route('/api/user/claim_daily', methods=['POST'])
def claim_daily():
    data = request.json or {}
    user_id = data.get("user_id")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT has_daily_pass, daily_streak, last_daily_claim, coins FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "Foydalanuvchi topilmadi"}), 404

    if user['has_daily_pass'] == 0:
        conn.close()
        return jsonify({"status": "error", "message": "Oldin Daily Pass sotib oling!"}), 400

    now = int(time.time())
    one_day = 86400
    if now - user['last_daily_claim'] < one_day:
        conn.close()
        return jsonify({"status": "error", "message": "Bugun allaqachon kunlik bonus oldingiz!"}), 400

    streak = user['daily_streak'] + 1
    reward = streak * 1000

    cursor.execute("UPDATE users SET coins = coins + ?, daily_streak = ?, last_daily_claim = ? WHERE user_id = ?", (reward, streak, now, user_id))
    conn.commit()
    cursor.execute("SELECT coins, daily_streak FROM users WHERE user_id = ?", (user_id,))
    updated = cursor.fetchone()
    conn.close()

    return jsonify({"status": "success", "coins": updated['coins'], "daily_streak": updated['daily_streak'], "reward": reward})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, coins, stars FROM users ORDER BY stars DESC, coins DESC LIMIT 10")
    top_users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "leaderboard": top_users})

@app.route('/api/game/open_case', methods=['POST'])
def open_case():
    data = request.json or {}
    user_id = data.get("user_id")
    case_type = data.get("case_type")

    prices = {
        'coin_1k': ('coins', 1000),
        'coin_5k': ('coins', 5000),
        'coin_20k': ('coins', 20000),
        'stars_5': ('stars', 5),
        'stars_20': ('stars', 20)
    }

    if case_type not in prices:
        return jsonify({"status": "error", "message": "Noto'g'ri quti"}), 400

    currency, price = prices[case_type]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT coins, stars FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or user[currency] < price:
        conn.close()
        return jsonify({"status": "error", "message": "Mabla'g yetarli emas"}), 400

    cursor.execute(f"UPDATE users SET {currency} = {currency} - ? WHERE user_id = ?", (price, user_id))

    win_type = 'coins'
    win_amount = 0
    rand = random.random()

    if currency == 'coins':
        if rand < 0.05:
            win_type = 'stars'
            win_amount = 1 if case_type != 'coin_20k' else 3
        else:
            win_amount = int(price * random.uniform(0.15, 0.6))
    else:
        if rand < 0.02:
            win_type = 'stars'
            win_amount = price * 2
        elif rand < 0.3:
            win_type = 'stars'
            win_amount = int(price * 0.4)
        else:
            win_amount = price * 1000

    if win_type == 'coins':
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (win_amount, user_id))
    else:
        cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (win_amount, user_id))

    conn.commit()
    cursor.execute("SELECT coins, stars FROM users WHERE user_id = ?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()

    return jsonify({
        "status": "success",
        "win_type": win_type,
        "win_amount": win_amount,
        "coins": updated_user['coins'],
        "stars": updated_user['stars']
    })

@app.route('/api/game/spin', methods=['POST'])
def spin():
    data = request.json or {}
    user_id = data.get("user_id")
    spin_type = data.get("spin_type")

    prices = {
        'coin_500': ('coins', 500),
        'coin_2500': ('coins', 2500),
        'stars_2': ('stars', 2),
        'stars_10': ('stars', 10)
    }

    if spin_type not in prices:
        return jsonify({"status": "error"}), 400

    currency, price = prices[spin_type]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT coins, stars FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or user[currency] < price:
        conn.close()
        return jsonify({"status": "error", "message": "Mabla'g yetarli emas"}), 400

    cursor.execute(f"UPDATE users SET {currency} = {currency} - ? WHERE user_id = ?", (price, user_id))

    rand = random.random()
    if currency == 'coins':
        win_type = 'stars' if rand < 0.03 else 'coins'
        win_amount = 1 if win_type == 'stars' else int(price * random.uniform(0.2, 0.7))
    else:
        win_type = 'stars' if rand < 0.1 else 'coins'
        win_amount = int(price * 1.5) if win_type == 'stars' else price * 800

    if win_type == 'coins':
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (win_amount, user_id))
    else:
        cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (win_amount, user_id))

    conn.commit()
    cursor.execute("SELECT coins, stars FROM users WHERE user_id = ?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()

    return jsonify({
        "status": "success",
        "win_type": win_type,
        "win_amount": win_amount,
        "coins": updated_user['coins'],
        "stars": updated_user['stars']
    })

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Player"
    args = message.text.split()

    conn = get_db()
    cursor = conn.cursor()

    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (referrer_id,))
                conn.commit()

    keyboard = InlineKeyboardMarkup()
    if WEBAPP_URL:
        keyboard.add(InlineKeyboardButton(text="🐹 Play Clicker Pro", web_app=WebAppInfo(url=WEBAPP_URL)))

    bot.send_message(
        message.chat.id,
        "👋 **Xush kelibsiz!**\n\nO'yinni boshlash uchun tugmani bosing:",
        reply_markup=keyboard
    )
    conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
