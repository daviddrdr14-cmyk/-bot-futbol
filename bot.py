import os, time, requests
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import telebot

# --- SERVIDOR PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot de Futbol Activo!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# --- BOT ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Mata el conflicto 409
bot.remove_webhook()
time.sleep(2)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "⚽ Bot de Predicciones HT listo!\nMándame un partido así:\nReal Madrid vs Barcelona")

@bot.message_handler(func=lambda m: True)
def analizar(m):
    partido = m.text
    if "vs" not in partido.lower():
        bot.reply_to(m, "Escríbelo así: Equipo vs Equipo")
        return

    bot.send_chat_action(m.chat.id, 'typing')
    
    # AQUÍ VA TU LÓGICA - Ejemplo de respuesta pro
    # Después le conectamos tu API de estadísticas real
    respuesta = f"""📊 *ANÁLISIS HT: {partido.upper()}*

🔥 Probabilidad Gol 1er Tiempo: 72%
⚽ Over 0.5 HT: CUOTA 1.40 - VALOR ALTO
🚩 Corners HT: Over 4.5

💰 *APUESTA RECOMENDADA: Over 0.5 Gol HT*

_Análisis basado en últimos 5 partidos._
"""
    bot.reply_to(m, respuesta, parse_mode="Markdown")

print("BOT LISTO - VERSION FINAL")
bot.infinity_polling(skip_pending=True)
