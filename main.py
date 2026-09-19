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

    if not user_id:
        return jsonify({'success': False, 'error': 'User ID mavjud emas'}), 400

    user = database.get_or_create_user(user_id, username, ref_by)
    return jsonify({
        'success': True,
        'user': {
            'userId': user['user_id'],
            'username': user['username'],
            'score': user['score'],
            'energy': user['energy'],
            'maxEnergy': user['max_energy'],
            'tapPower': user['tap_power']
        }
    })

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json or {}
    user_id = data.get('userId')
    if not user_id:
        return jsonify({'success': False, 'error': 'User ID mavjud emas'}), 400

    result = database.process_tap(user_id)
    return jsonify(result)

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json or {}
    user_id = data.get('userId')
    reward = data.get('reward', 0)
    
    if not user_id:
        return jsonify({'success': False, 'error': 'User ID mavjud emas'}), 400

    # Narxi 200 coin çıxılıb, yutuq qo'shiladi (reward - 200)
    net_change = reward - 200
    res = database.update_score_and_energy(user_id, net_change)
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
