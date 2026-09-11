import os
import threading
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import database as db

app = Flask(__name__)
CORS(app)

# Environment variable'lardan token va admin ID'larni olish
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(i) for i in os.environ.get("ADMIN_IDS", "").split(",") if i.isdigit()]

# ==================== TELEGRAM BOT POLLING ====================
def run_bot_polling():
    if not BOT_TOKEN:
        print("BOT_TOKEN topilmadi! Environment variables ni tekshiring.")
        return

    offset = 0
    print("Telegram Bot Polling ishga tushdi...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35).json()

            if response.get("ok"):
                for result in response.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    username = message.get("from", {}).get("username", "User")

                    if text == "/start":
                        # Foydalanuvchini bazada yaratish yoki olish
                        db.get_or_create_user(chat_id, username)

                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": chat_id,
                            "text": f"Xush kelibsiz, @{username}! Cyber Pro Hub Mini App'ni ochish uchun pastdagi tugmani bosing.",
                            "reply_markup": {
                                "inline_keyboard": [[
                                    {"text": "🚀 Cyber Pro Hub Mini App", "web_app": {"url": "https://telegram-bot-7n6t.onrender.com"}}
                                ]]
                            }
                        }
                        requests.post(send_url, json=payload)
        except Exception as e:
            print(f"Bot Polling xatoligi: {e}")
            time.sleep(3)

# Bot pollingni orqa fonda (thread) yurgizish
threading.Thread(target=run_bot_polling, daemon=True).start()


# ==================== FLASK API ENDPOINTS ====================

@app.route("/")
def home():
    return "Cyber Pro Hub Backend Status: ONLINE 🟢"

@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user_data = db.get_or_create_user(user_id)
    return jsonify(user_data)

@app.route("/api/tap", methods=["POST"])
def tap():
    data = request.json or {}
    user_id = data.get("user_id")
    coins_added = data.get("coins_added", 1)
    energy_used = data.get("energy_used", 1)

    if not user_id:
        return jsonify({"error": "user_id kerak"}), 400

    success = db.update_user_tap(user_id, coins_added, energy_used)
    if success:
        return jsonify({"status": "success"})
    return jsonify({"error": "Energiya yetarli emas"}), 400

@app.route("/api/wallet", methods=["POST"])
def wallet():
    data = request.json or {}
    user_id = data.get("user_id")
    wallet_address = data.get("wallet", "")

    if not user_id:
        return jsonify({"error": "user_id kerak"}), 400

    db.update_user_wallet(user_id, wallet_address)
    return jsonify({"status": "success", "wallet": wallet_address})

@app.route("/api/boost", methods=["POST"])
def boost():
    data = request.json or {}
    user_id = data.get("user_id")
    boost_type = data.get("boost_type")
    cost = data.get("cost", 0)

    success, message = db.buy_boost_upgrade(user_id, boost_type, cost)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"error": message}), 400

@app.route("/api/claim-daily", methods=["POST"])
def claim_daily():
    data = request.json or {}
    user_id = data.get("user_id")

    success, message = db.claim_daily_bonus(user_id)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"error": message}), 400

@app.route("/api/task", methods=["POST"])
def complete_task():
    data = request.json or {}
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    reward = data.get("reward", 500)

    success, message = db.complete_user_task(user_id, task_id, reward)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"error": message}), 400

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    top_users = db.get_top_leaderboard()
    return jsonify(top_users)

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    stats = db.get_admin_stats()
    return jsonify(stats)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
