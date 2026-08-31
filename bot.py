import os, time, requests
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot HT Live - SofaScore REAL"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN OK: {bool(TOKEN)}", flush=True)

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# IDS REALES SOFASCORE
TEAMS = {
    "monterrey": 19589, "rayados": 19589, "mty": 19589,
    "san luis": 122124, "atletico san luis": 122124, "atletico de san luis": 122124,
    "america": 19595, "chivas": 19593, "tigres": 19592, "cruz azul": 19594,
    "aston villa": 40, "arsenal": 42, "man city": 17, "liverpool": 44, 
    "barcelona": 2817, "real madrid": 2829
}

def get_id(n):
    n = n.lower().strip()
    for k,v in TEAMS.items():
        if k in n or n in k: return v
    if "mont" in n: return 19589
    if "luis" in n: return 122124
    return None

def stats(n):
    tid = get_id(n)
    if not tid: return None
    try:
        r = requests.get(f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0", 
                         headers={"User-Agent":"Mozilla/5.0"}, timeout=15).json()
        evs = r.get('events', [])[:5]
        if not evs: return None
        ht = sum(1 for e in evs if e['homeScore'].get('period1',0)+e['awayScore'].get('period1',0)>0)
        return {"name": n.title(), "ht": int(ht/len(evs)*100) if evs else 0, "c": ht, "t": len(evs)}
    except Exception as e:
        print(f"ERR {e}", flush=True)
        return None

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v = [x.strip() for x in m.text.split("vs",1)]
    print(f"RECIBIDO: {l} vs {v} -> {get_id(l)} {get_id(v)}", flush=True)
    s1 = stats(l); s2 = stats(v)
    if not s1 or not s2:
        bot.reply_to(m, "No encontré uno. Prueba: monterrey, san luis, america, arsenal, barcelona")
        return
    comb = int((s1['ht']+s2['ht'])/2)
    bot.reply_to(m, f"📊 *{s1['name']} vs {s2['name']} - SOFASCORE REAL*\n\n{s1['name']}: {s1['ht']}% ({s1['c']}/{s1['t']}) HT\n{s2['name']}: {s2['ht']}%\n\n🔥 *COMBINADO HT: {comb}%* {'FUERTE ✅' if comb>=65 else 'MEDIO ⚠️' if comb>=50 else 'NO ❌'}", parse_mode="Markdown")

print("BOT FINAL LISTO - ESPERANDO MENSAJES", flush=True)
bot.infinity_polling(skip_pending=True)
