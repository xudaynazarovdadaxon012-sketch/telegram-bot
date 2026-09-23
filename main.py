import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.environ.get("BOT_TOKEN")
# Shu yerga Netlify/Vercel'dagi HTML saytingiz linkini yozing:
WEBAPP_URL = "https://telegram-bot-7n6t.onrender.com/miniapp.html"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(
        text="🎮 CyberPulse O'yinini Boshlash", 
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        f"Salom {message.from_user.first_name}! 👋\n\nCyberPulse 3D Mini App o'yiniga xush kelibsiz! O'ynash uchun pastdagi tugmani bosing:",
        reply_markup=markup
    )

# Render port so'rab xato bermasligi uchun kichik server
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("Bot va server ishga tushdi...")
    bot.infinity_polling()
