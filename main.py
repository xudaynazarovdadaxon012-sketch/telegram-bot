import os
import random
import threading
import telebot
from flask import Flask, request, jsonify, render_template_string
from database import init_db, get_or_create_user, update_user_progress, update_user_score, process_upgrade

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

init_db()

@app.route('/')
def index():
    with open('miniapp.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/get_user', methods=['GET'])
def get_user():
    tg_id = request.args.get('tg_id', 'demo_user')
    user = get_or_create_user(tg_id)
    return jsonify(user)

@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id', 'demo_user')
    score = data.get('score', 0)
    energy = data.get('energy', 1000)
    tap_level = data.get('tap_level', 1)
    max_energy = data.get('max_energy', 1000)

    update_user_progress(tg_id, score, energy, tap_level, max_energy)
    return jsonify({'status': 'ok'})

@app.route('/open_case', methods=['POST'])
def open_case():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id', 'demo_user')
    price = 300

    user = get_or_create_user(tg_id)

    if user['score'] < price:
        return jsonify({'error': 'Mablag\' yetarli emas!'}), 400

    prizes = [50, 100, 200, 500, 1000, 5000]
    weights = [45, 30, 15, 7, 2.8, 0.2]
    win_amount = random.choices(prizes, weights=weights)[0]

    new_score = user['score'] - price + win_amount
    update_user_score(tg_id, new_score)

    return jsonify({'win': win_amount, 'new_score': new_score})

@app.route('/buy_upgrade', methods=['POST'])
def buy_upgrade():
    data = request.get_json(silent=True) or {}
    tg_id = data.get('tg_id', 'demo_user')
    upgrade_type = data.get('type')

    updated_user = process_upgrade(tg_id, upgrade_type)
    return jsonify(updated_user)

if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = telebot.types.InlineKeyboardMarkup()
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        web_app = telebot.types.WebAppInfo(url=render_url)
        markup.add(telebot.types.InlineKeyboardButton("🎮 Play Crypto Game", web_app=web_app))
        bot.reply_to(message, "⚡ Welcome to Premium Mini App!", reply_markup=markup)

def run_bot():
    if bot:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Bot error: {e}")

if __name__ == '__main__':
    if bot:
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
