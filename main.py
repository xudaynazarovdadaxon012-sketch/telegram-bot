from flask import Flask, render_template, request, jsonify
from database import init_db, get_user_data, update_user_data, deduct_score

# template_folder='.' orqali html faylni papkasiz to'g'ridan-to'g'ri o'qiydi
app = Flask(__name__, template_folder='.')

# Server ishga tushganda bazani tayyorlash
init_db()

@app.route('/')
def index():
    return render_template('miniapp.html')

@app.route('/api/get_user', methods=['POST'])
def api_get_user():
    data = request.json
    return jsonify(get_user_data(str(data.get('tg_id'))))

@app.route('/api/save_user', methods=['POST'])
def api_save_user():
    d = request.json
    update_user_data(str(d.get('tg_id')), d.get('score'), d.get('energy'), d.get('pushups'))
    return jsonify({'status': 'success'})

@app.route('/api/request_stars', methods=['POST'])
def api_request_stars():
    d = request.json
    new_score = deduct_score(str(d.get('tg_id')), d.get('cost'))
    if new_score is not None:
        return jsonify({'status': 'success', 'new_score': new_score})
    return jsonify({'status': 'error', 'message': 'Balans yetarli emas'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
