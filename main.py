from flask import Flask, request, jsonify
from flask_cors import CORS
import database

app = Flask(__name__)
CORS(app)

@app.route('/api/sync', methods=['POST'])
def sync():
    data = request.json or {}
    user_id = data.get('userId')
    username = data.get('username', "O'yinchi")
    ref_by = data.get('refBy')

    if not user_id: return jsonify({'success': False}), 400

    user = database.get_or_create_user(user_id, username, ref_by)
    return jsonify({
        'success': True,
        'user': {
            'userId': user['user_id'],
            'username': user['username'],
            'score': user['score'],
            'energy': user['energy'],
            'maxEnergy': user['max_energy'],
            'tapPower': user['tap_power'],
            'isVip': user.get('is_vip', False)
        }
    })

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json or {}
    user_id = data.get('userId')
    if not user_id: return jsonify({'success': False}), 400
    return jsonify(database.process_tap(user_id))

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json or {}
    user_id = data.get('userId')
    reward = data.get('reward', 0)
    cost = data.get('cost', 100)
    if not user_id: return jsonify({'success': False}), 400
    return jsonify(database.update_score_and_energy(user_id, reward, cost))

@app.route('/api/daily', methods=['POST'])
def daily():
    data = request.json or {}
    user_id = data.get('userId')
    if not user_id: return jsonify({'success': False}), 400
    return jsonify(database.claim_daily(user_id))

@app.route('/api/ad-reward', methods=['POST'])
def ad_reward():
    data = request.json or {}
    user_id = data.get('userId')
    amount = data.get('amount', 300)
    if not user_id: return jsonify({'success': False}), 400
    return jsonify(database.add_ad_reward(user_id, amount))

@app.route('/api/buy-boost', methods=['POST'])
def buy_boost():
    data = request.json or {}
    user_id = data.get('userId')
    boost_type = data.get('type')
    if not user_id or not boost_type: return jsonify({'success': False}), 400
    return jsonify(database.buy_boost(user_id, boost_type))

@app.route('/api/exchange-stars', methods=['POST'])
def exchange_stars():
    data = request.json or {}
    user_id = data.get('userId')
    if not user_id: return jsonify({'success': False}), 400
    return jsonify(database.exchange_to_stars(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
