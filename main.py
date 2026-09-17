from flask import Flask, render_template_string, request, jsonify
from database import init_db, get_user_data, update_user_data, deduct_score

app = Flask(__name__)

# Server ishga tushganda bazani tayyorlash
init_db()

# To'liq dizayn va interfeys
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Crypto Empire Pro - AI Fitness & Tap</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js" crossorigin="anonymous"></script>
    
    <style>
        :root {
            --bg: #07090e; --card-bg: rgba(21, 29, 42, 0.7);
            --card-border: rgba(255, 255, 255, 0.12); --accent: #ffb703;
            --accent-glow: rgba(255, 183, 3, 0.4); --purple: #8b5cf6;
            --green: #10b981; --text: #ffffff;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg); background-image: radial-gradient(circle at 50% 10%, #1e1b4b 0%, var(--bg) 70%);
            color: var(--text); margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh;
            user-select: none; overflow: hidden; position: relative;
        }
        .header { text-align: center; padding: 15px; background: var(--card-bg); backdrop-filter: blur(20px); border-bottom: 1px solid var(--card-border); }
        .balance-box { font-size: 38px; font-weight: 900; color: var(--accent); text-shadow: 0 0 25px var(--accent-glow); }
        .nav-tabs { display: flex; justify-content: space-around; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(20px); padding: 8px 5px; border-bottom: 1px solid var(--card-border); }
        .tab-btn { background: none; border: none; color: #94a3b8; font-size: 11px; font-weight: 700; cursor: pointer; padding: 8px 10px; border-radius: 12px; }
        .tab-btn.active { color: #fff; background: linear-gradient(135deg, rgba(255,183,3,0.25), rgba(139,92,246,0.25)); border: 1px solid rgba(255,255,255,0.2); }
        .tab-content { display: none; flex-direction: column; align-items: center; justify-content: center; flex-grow: 1; padding: 15px; overflow-y: auto; }
        .tab-content.active { display: flex; }
        .coin-container { perspective: 1000px; display: flex; justify-content: center; align-items: center; }
        .coin { width: 180px; height: 180px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #ffe169 0%, #ffb703 50%, #d97706 100%); display: flex; align-items: center; justify-content: center; font-size: 75px; box-shadow: 0 20px 40px rgba(0,0,0,0.7), 0 0 60px var(--accent-glow); cursor: pointer; animation: coinFloat 3s ease-in-out infinite; }
        .coin:active { transform: scale(0.88); }
        @keyframes coinFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .floating-num { position: absolute; color: #fff; font-weight: 900; font-size: 28px; pointer-events: none; z-index: 99; animation: floatUp 0.8s forwards ease-out; }
        @keyframes floatUp { 0% { opacity: 1; transform: translateY(0) scale(1); } 100% { opacity: 0; transform: translateY(-80px) scale(1.4); } }
        .glass-card { width: 100%; max-width: 330px; background: var(--card-bg); backdrop-filter: blur(20px); padding: 14px; border-radius: 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--card-border); }
        .action-btn { background: linear-gradient(135deg, #ffb703, #fb8500); border: none; padding: 8px 14px; border-radius: 10px; font-weight: 900; color: #000; cursor: pointer; }
        .camera-wrapper { position: relative; width: 100%; max-width: 320px; height: 380px; border-radius: 20px; overflow: hidden; border: 2px solid var(--purple); background: #000; display: flex; align-items: center; justify-content: center; }
        #webcam { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
        .fitness-overlay { position: absolute; bottom: 15px; left: 15px; right: 15px; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(10px); padding: 10px; border-radius: 12px; text-align: center; }
        .footer { padding: 14px 20px; background: var(--card-bg); border-top: 1px solid var(--card-border); }
        .progress-bar { width: 100%; background: rgba(255,255,255,0.05); height: 8px; border-radius: 8px; overflow: hidden; }
        .progress-fill { width: 100%; height: 100%; background: linear-gradient(90deg, #ffb703, #10b981); }
    </style>
</head>
<body>
    <div class="header">
        <div class="balance-box">🪙 <span id="score">0</span></div>
    </div>
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab(event, 'tap')">⚡ Tap</button>
        <button class="tab-btn" onclick="switchTab(event, 'fitness')">🤖 AI Fitness</button>
        <button class="tab-btn" onclick="switchTab(event, 'stars')">⭐ Stars</button>
    </div>
    <div id="tap" class="tab-content active">
        <div class="coin-container"><div class="coin" id="coinBtn">🪙</div></div>
    </div>
    <div id="fitness" class="tab-content">
        <h3 style="margin-top: 0; color: var(--purple);">💪 Otjimaniya & AI</h3>
        <p style="color: #94a3b8; font-size: 11px; text-align: center;">Kameraga qarab otjimaniya qiling, har biri <b>+50 🪙</b>!</p>
        <div class="camera-wrapper">
            <video id="webcam" autoplay playsinline></video>
            <div class="fitness-overlay">
                <div style="font-size: 13px; color: #94a3b8;">Sanoq: <b id="pushupCount" style="color: var(--accent); font-size: 18px;">0</b></div>
                <div id="aiStatus" style="font-size: 11px; color: var(--green);">Kamera ishga tushmoqda...</div>
            </div>
        </div>
    </div>
    <div id="stars" class="tab-content">
        <h3>⭐ Telegram Stars</h3>
        <div class="glass-card">
            <div><div><b>⭐ 1 Telegram Star</b></div><small style="color: #94a3b8;">Narxi: 5,000 🪙</small></div>
            <button class="action-btn" onclick="withdrawStars(1, 5000)">Olish</button>
        </div>
    </div>
    <div class="footer">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12px; font-weight: 700;">
            <span>⚡ Energiya</span><span><span id="energy">500</span> / <span id="maxEnergy">500</span></span>
        </div>
        <div class="progress-bar"><div class="progress-fill" id="energyFill"></div></div>
    </div>
    <script>
        let tg = window.Telegram?.WebApp;
        if(tg) { tg.expand(); tg.ready(); }
        let userId = tg?.initDataUnsafe?.user?.id?.toString() || "demo_user_123";
        let score = 0, energy = 500, maxEnergy = 500, pushups = 0, exerciseState = "up";

        async function loadUserData() {
            try {
                let res = await fetch('/api/get_user', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ tg_id: userId }) });
                let data = await res.json();
                score = data.score; energy = data.energy; pushups = data.pushups;
                document.getElementById('pushupCount').innerText = pushups;
                updateUI();
            } catch (e) {}
        }
        async function saveUserData() {
            try {
                await fetch('/api/save_user', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ tg_id: userId, score: score, energy: energy, pushups: pushups }) });
            } catch (e) {}
        }
        function updateUI() {
            document.getElementById('score').innerText = score;
            document.getElementById('energy').innerText = energy;
            document.getElementById('maxEnergy').innerText = maxEnergy;
            document.getElementById('energyFill').style.width = Math.max(0, Math.min(100, (energy / maxEnergy * 100))) + '%';
        }
        document.getElementById('coinBtn').addEventListener('pointerdown', (e) => {
            if (energy >= 1) {
                score += 1; energy -= 1; updateUI(); saveUserData();
                let f = document.createElement('div'); f.className = 'floating-num'; f.innerText = '+1';
                f.style.left = (e.clientX - 15) + 'px'; f.style.top = (e.clientY - 30) + 'px';
                document.body.appendChild(f); setTimeout(() => f.remove(), 800);
            }
        });
        const videoElement = document.getElementById('webcam');
        let poseInstance = null;
        function onResults(results) {
            if (!results.poseLandmarks) return;
            let sh = results.poseLandmarks[11], hip = results.poseLandmarks[23];
            if (sh && hip) {
                let h = Math.abs(sh.y - hip.y);
                if (h < 0.35 && exerciseState === "up") exerciseState = "down";
                else if (h >= 0.35 && exerciseState === "down") {
                    exerciseState = "up"; pushups++; score += 50; updateUI(); saveUserData();
                    document.getElementById('pushupCount').innerText = pushups;
                }
            }
        }
        async function initCamera() {
            try {
                const pose = new Pose({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}` });
                pose.setOptions({ modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5 });
                pose.onResults(onResults);
                const camera = new Camera(videoElement, { onFrame: async () => { await pose.send({image: videoElement}); }, width: 320, height: 380 });
                camera.start();
            } catch (err) { document.getElementById('aiStatus').innerText = "Kamera ishlamadi!"; }
        }
        async function withdrawStars(stars, cost) {
            if (score < cost) { alert("Coin yetarli emas!"); return; }
            let res = await fetch('/api/request_stars', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ tg_id: userId, stars, cost }) });
            let data = await res.json();
            if(res.ok) { score = data.new_score; updateUI(); alert("✅ Ariza qabul qilindi!"); }
        }
        function switchTab(e, name) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(name).classList.add('active'); e.target.classList.add('active');
            if(name === 'fitness' && !poseInstance) { initCamera(); poseInstance = true; }
        }
        setInterval(() => { if (energy < maxEnergy) { energy = Math.min(maxEnergy, energy + 1); updateUI(); saveUserData(); } }, 3000);
        loadUserData();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get_user', methods=['POST'])
def api_get_user():
    return jsonify(get_user_data(str(request.json.get('tg_id'))))

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
