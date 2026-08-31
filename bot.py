import os, time
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

Thread(target=run, daemon=True).start()

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
bot.remove_webhook()
time.sleep(1)

@bot.message_handler(func=lambda m: True)
def _ (m):
    bot.reply_to(m, f"Funciona: {m.text}")

print("BOT LISTO - 12:41")
bot.infinity_polling(skip_pending=True)
