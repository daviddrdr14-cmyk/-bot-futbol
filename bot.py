from flask import Flask
from threading import Thread
import os
from dotenv import load_dotenv
import telebot

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda m: True)
def hola(m):
    bot.reply_to(m, f"Recibido: {m.text} - Bot en Render funcionando!")

print("BOT LISTO")
bot.infinity_polling()
