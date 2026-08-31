from flask import Flask
from threading import Thread
import os
import re
import time
import requests
import telebot
import unicodedata
from dotenv import load_dotenv

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de futbol funcionando! ⚽"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# --- TU BOT ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("ERROR: No hay BOT_TOKEN en Environment")
else:
    print(f"Token cargado: {TOKEN[:10]}...")

bot = telebot.TeleBot(TOKEN)

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.google.com/"}
EQUIPOS = {"barcelona": (2817, "Barcelona"), "real madrid": (2829, "Real Madrid"), "arsenal": (42, "Arsenal"), "aston villa": (40, "Aston Villa"), "manchester city": (17, "Man City"), "liverpool": (44, "Liverpool")}

def norm(t):
    t = t.lower()
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.strip()

def buscar(n):
    return EQUIPOS.get(norm(n))

@bot.message_handler(func=lambda m: True)
def go(m):
    txt = norm(m.text)
    if "vs" not in txt:
        bot.reply_to(m, "Escribe: Equipo vs Equipo\nEj: Barcelona vs Real Madrid")
        return
    try:
        a,b = re.split(r'\s+vs\s+', txt)
        r1 = buscar(a)
        r2 = buscar(b)
        if not r1 or not r2:
            bot.reply_to(m, "❌ No encontré uno de los equipos. Intenta con otro.")
            return
        id1,n1 = r1
        id2,n2 = r2
        
        # Aquí va tu lógica de análisis, te
