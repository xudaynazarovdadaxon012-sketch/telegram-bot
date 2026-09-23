import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Token Render Environment Variables'dan olinadi
TOKEN = os.environ.get("BOT_TOKEN")

# WebApp havolasi (Netlify/Vercel/GitHub Pages bergan https linkni shu yerga yozasiz)
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

if __name__ == "__main__":
    print("Bot Render'da muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
