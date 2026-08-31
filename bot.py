import os, time, requests
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot HT Live - SofaScore REAL V2"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

TEAMS = {
    "monterrey": 19589, "rayados": 19589, "mty": 19589,
    "san luis": 122124, "atletico san luis": 122124,
    "america": 19595, "chivas": 19593, "guadalajara": 19593,
    "tigres": 19592, "cruz azul": 19594, "pumas": 19590,
    "arsenal": 42, "aston villa": 40, "man city": 17, "liverpool": 44,
    "barcelona": 2817, "real madrid": 2829
}

def get_id(n):
    n = n.lower().strip()
    for k,v in TEAMS.items():
        if k in n or n in k: return v
    return None

def stats(n):
    tid = get_id(n)
    if not tid: 
        print(f"ID NO ENCONTRADO PARA: {n}", flush=True)
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com"
        }
        url = f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0"
        r = requests.get(url, headers=headers, timeout=15)
        print(f"SOFASCORE {n} {tid} -> Status {r.status_code}", flush=True)
        data = r.json()
        evs = data.get('events', [])[:5]
        print(f"EVENTOS {n}: {len(evs)}", flush=True)
        if not evs: return None
        ht = sum(1 for e in evs if e.get('homeScore',{}).get('period1',0)+e.get('awayScore',{}).get('period1',0)>0)
        return {"name": n.title(), "ht": int(ht/len(evs)*100), "c": ht, "t": len(evs)}
    except Exception as e:
        print(f"ERR stats {n}: {e}", flush=True)
        return None

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    try:
        l,v = [x.strip() for x in m.text.lower().split("vs",1)]
        print(f"RECIBIDO: {l} vs {v}", flush=True)
        s1 = stats(l); s2 = stats(v)
        if not s1:
            bot.reply_to(m, f"⚠️ SofaScore bloqueó a {l.title()}. Intenta de nuevo en 10 seg. ID: {get_id(l)}")
            return
        if not s2:
            bot.reply_to(m, f"⚠️ SofaScore bloqueó a {v.title()}. Intenta de nuevo. ID: {get_id(v)}")
            return
        comb = int((s1['ht']+s2['ht'])/2)
        bot.reply_to(m, f"📊 *{s1['name']} vs {s2['name']} - SOFASCORE REAL*\n\n{s1['name']}: {s1['ht']}% ({s1['c']}/{s1['t']}) HT\n{s2['name']}: {s2['ht']}% ({s2['c']}/{s2['t']}) HT\n\n🔥 *COMBINADO HT: {comb}%* {'FUERTE ✅' if comb>=65 else 'MEDIO ⚠️' if comb>=50 else 'NO ❌'}", parse_mode="Markdown")
    except Exception as e:
        print(f"ERR handler: {e}", flush=True)

print("BOT V2 LISTO - CON HEADERS SOFASCORE", flush=True)
bot.infinity_polling(skip_pending=True)
