from flask import Flask, request, jsonify
from flask_cors import CORS
import database

app = Flask(__name__)
CORS(app)

@app.route('/api/sync', methods=['POST'])
def sync():
    data = request.json or {}
    user = database.get_or_create_user(data.get('userId'), data.get('username', "O'yinchi"))
    return jsonify({'success': True, 'user': user})

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json or {}
    return jsonify(database.process_tap(data.get('userId'), data.get('count', 1)))

@app.route('/api/daily', methods=['POST'])
def daily():
    data = request.json or {}
    return jsonify(database.claim_daily(data.get('userId')))

@app.route('/api/buy-boost', methods=['POST'])
def buy_boost():
    data = request.json or {}
    return jsonify(database.buy_boost(data.get('userId'), data.get('type')))

@app.route('/api/exchange-stars', methods=['POST'])
def exchange_stars():
    data = request.json or {}
    return jsonify(database.exchange_coins_for_stars(data.get('userId'), data.get('stars', 5)))

@app.route('/api/theme', methods=['POST'])
def theme():
    data = request.json or {}
    return jsonify(database.set_theme(data.get('userId'), data.get('theme')))

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify({'success': True, 'leaderboard': database.get_leaderboard()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
