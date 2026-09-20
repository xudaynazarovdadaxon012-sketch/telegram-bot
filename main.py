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
    return jsonify({'success': True, 'user': user})

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json or {}
    count = data.get('count', 1)
    return jsonify(database.process_tap(data.get('userId'), count))

@app.route('/api/daily', methods=['POST'])
def daily():
    data = request.json or {}
    return jsonify(database.claim_daily(data.get('userId')))

@app.route('/api/task', methods=['POST'])
def task():
    data = request.json or {}
    return jsonify(database.complete_task(data.get('userId'), data.get('taskId')))

@app.route('/api/buy-boost', methods=['POST'])
def buy_boost():
    data = request.json or {}
    return jsonify(database.buy_boost(data.get('userId'), data.get('type')))

@app.route('/api/theme', methods=['POST'])
def theme():
    data = request.json or {}
    return jsonify(database.set_theme(data.get('userId'), data.get('theme')))

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify({'success': True, 'leaderboard': database.get_leaderboard()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
