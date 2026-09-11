import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# database.py faylidagi funksiyalarni import qilamiz
from database import (
    get_or_create_user, 
    update_user_tap, 
    update_user_wallet,
    buy_boost_upgrade, 
    claim_daily_bonus, 
    complete_user_task,
    get_top_leaderboard, 
    get_admin_stats, 
    get_all_user_ids
)

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN"))
ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]

INITIAL_TASKS = [
    {"id": "task_1", "title": "Telegram kanalga obuna bo'ling", "reward": 500},
    {"id": "task_2", "title": "Do'stingizni taklif qiling", "reward": 1000}
]

# 1. Foydalanuvchi ma'lumotlarini olish
@app.route('/api/get_user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username', type=str, default="User")
    if not user_id:
        return jsonify({"success": False, "message": "user_id kiritilmadi"}), 400

    usr = get_or_create_user(user_id, username)
    is_admin = user_id in ADMIN_IDS

    return jsonify({
        "success": True,
        "coins": usr["coins"],
        "energy": usr["energy"],
        "max_energy": usr["max_energy"],
        "tap_level": usr["tap_level"],
        "wallet": usr["wallet"],
        "last_daily_claim": usr["last_daily_claim"],
        "tasks": INITIAL_TASKS,
        "completed_tasks": usr["completed_tasks"],
        "ref_link": f"https://t.me/CyberPro_bot?start={user_id}",
        "is_admin": is_admin
    })

# 2. Tap qilish
@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json or {}
    user_id = data.get('user_id')
    amount = data.get('amount', 1)

    if not user_id:
        return jsonify({"success": False, "message": "User ID yetishmayapti"}), 400

    usr = get_or_create_user(user_id)
    tap_power = usr["tap_level"] * amount

    success = update_user_tap(user_id, coins_added=tap_power, energy_used=tap_power)
    if not success:
        return jsonify({"success": False, "message": "Energiya yetarli emas"}), 400

    updated_usr = get_or_create_user(user_id)
    return jsonify({
        "success": True, 
        "coins": updated_usr["coins"], 
        "energy": updated_usr["energy"]
    })

# 3. Boost sotib olish
@app.route('/api/buy_boost', methods=['POST'])
def buy_boost():
    data = request.json or {}
    user_id = data.get('user_id')
    boost_type = data.get('boost_type')

    usr = get_or_create_user(user_id)

    cost = 0
    if boost_type == 'multitap':
        cost = usr["tap_level"] * 100
    elif boost_type == 'max_energy':
        cost = 500
    else:
        return jsonify({"success": False, "message": "Noma'lum boost turi"}), 400

    success, msg = buy_boost_upgrade(user_id, boost_type, cost)
    return jsonify({"success": success, "message": msg})

# 4. Hamyonni saqlash
@app.route('/api/connect_wallet', methods=['POST'])
def connect_wallet():
    data = request.json or {}
    user_id = data.get('user_id')
    wallet = data.get('wallet_address', '').strip()

    if not user_id:
        return jsonify({"success": False, "message": "Xatolik"}), 400

    update_user_wallet(user_id, wallet)
    return jsonify({"success": True, "message": "Hamyon muvaffaqiyatli saqlandi! 💎"})

# 5. Vazifani bajarish
@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    data = request.json or {}
    user_id = data.get('user_id')
    task_id = data.get('task_id')

    task = next((t for t in INITIAL_TASKS if t["id"] == task_id), None)
    if not task:
        return jsonify({"success": False, "message": "Vazifa topilmadi"}), 404

    success, msg = complete_user_task(user_id, task_id, task["reward"])
    return jsonify({"success": success, "message": msg})

# 6. Kunlik bonus olish
@app.route('/api/claim_daily', methods=['POST'])
def claim_daily():
    data = request.json or {}
    user_id = data.get('user_id')

    success, msg = claim_daily_bonus(user_id, reward=1000)
    return jsonify({"success": success, "message": msg})

# 7. TOP 10 Liderlar
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    top_list = get_top_leaderboard(limit=10)
    return jsonify({"success": True, "leaderboard": top_list})

# 8. Admin Profil API (Instagram Style)
@app.route('/api/admin/insta_profile', methods=['GET'])
def admin_insta_profile():
    admin_id = request.args.get('user_id', type=int)
    if admin_id not in ADMIN_IDS:
        return jsonify({"success": False, "message": "Ruxsat berilmagan"}), 403

    stats = get_admin_stats()
    return jsonify({
        "success": True,
        "profile": {
            "posts": stats["posts"],
            "followers": stats["followers"],
            "following": stats["following"],
            "bio": stats["bio"]
        },
        "users": stats["users"]
    })

# 9. Admin Direct xabar yuborish
@app.route('/api/admin/send_direct', methods=['POST'])
def send_direct():
    data = request.json or {}
    admin_id = data.get('admin_id')
    target_user_id = data.get('target_user_id')
    message = data.get('message')

    if admin_id not in ADMIN_IDS:
        return jsonify({"success": False, "message": "Ruxsat berilmagan"}), 403

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": target_user_id, "text": f"💬 Admin xabari:\n\n{message}"}
    res = requests.post(url, json=payload)

    if res.status_code == 200:
        return jsonify({"success": True, "message": "Direct xabar yuborildi! ✉️"})
    return jsonify({"success": False, "message": "Xabar yuborishda xatolik"}), 500

# 10. Admin Broadcast xabar yuborish
@app.route('/api/admin/broadcast', methods=['POST'])
def send_broadcast():
    data = request.json or {}
    admin_id = data.get('admin_id')
    message = data.get('message')

    if admin_id not in ADMIN_IDS:
        return jsonify({"success": False, "message": "Ruxsat berilmagan"}), 403

    all_ids = get_all_user_ids()
    count = 0
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for u_id in all_ids:
        payload = {"chat_id": u_id, "text": f"📢 E'lon:\n\n{message}"}
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            count += 1

    return jsonify({"success": True, "message": f"Xabar {count} ta foydalanuvchiga yuborildi! 🚀"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
