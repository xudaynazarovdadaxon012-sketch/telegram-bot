import os
import time
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database as db

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8898979946]
BASE_URL = "https://telegram-bot-7n6t.onrender.com"

# ==================== TELEGRAM BOT POLLING ====================
def run_bot_polling():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        return

    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except Exception as e:
        print(f"Webhook reset: {e}")

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=35).json()

            if res.get("ok"):
                for result in res.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    username = message.get("from", {}).get("username", "User")

                    if not chat_id:
                        continue

                    if text.startswith("/start"):
                        referrer_id = None
                        parts = text.split()
                        if len(parts) > 1 and parts[1].startswith("ref_"):
                            try:
                                referrer_id = int(parts[1].replace("ref_", ""))
                            except ValueError:
                                pass

                        db.get_or_create_user(chat_id, username, referrer_id)
                        
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": chat_id,
                            "text": f"👋 Xush kelibsiz, @{username}!\n\nCyber Pro Hub Mini App orqali tangalaringizni yig'ing.",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [{"text": "🚀 Mini App'ni ochish", "web_app": {"url": f"{BASE_URL}/miniapp.html"}}],
                                    [{"text": "👥 Do'stlarni taklif qilish", "url": f"https://t.me/share/url?url=https://t.me/CyberProHubBot?start=ref_{chat_id}"}]
                                ]
                            }
                        }
                        requests.post(send_url, json=payload)
        except Exception as e:
            time.sleep(3)

threading.Thread(target=run_bot_polling, daemon=True).start()

# ==================== ROUTING ====================
@app.route("/")
def home():
    return send_from_directory('.', 'miniapp.html')

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory('.', filename)

# ==================== API ENDPOINTLARI ====================
@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.get_or_create_user(user_id)
    return jsonify({"status": "success", "data": user})

@app.route("/api/tap", methods=["POST"])
def tap():
    data = request.json or {}
    user_id = data.get("user_id")
    coins_added = data.get("coins_added", 1)
    energy_used = data.get("energy_used", 1)

    if not user_id or coins_added > 50:
        return jsonify({"error": "Noto'g'ri so'rov"}), 400

    if db.update_user_tap(user_id, coins_added, energy_used):
        return jsonify({"status": "success"})
    return jsonify({"error": "Energiya yetarli emas"}), 400

@app.route("/api/pay/ton", methods=["POST"])
def pay_ton():
    data = request.json or {}
    user_id = data.get("user_id")
    tx_hash = data.get("tx_hash")
    amount = data.get("amount", 0.0)
    item_type = data.get("item_type", "BUY_COINS")

    if not user_id or not tx_hash or amount <= 0:
        return jsonify({"error": "Ma'lumot kam"}), 400

    success, msg = db.process_ton_purchase(user_id, tx_hash, float(amount), item_type)
    if success:
        return jsonify({"status": "success", "message": msg})
    return jsonify({"error": msg}), 400

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    user_id = request.args.get("user_id", type=int)
    if user_id not in ADMIN_IDS:
        return jsonify({"error": "Ruxsat yo'q"}), 403
    return jsonify({"status": "success", "stats": db.get_admin_stats()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
