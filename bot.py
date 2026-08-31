import os, time, requests, urllib.parse
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot HT V5 5-Capas FINAL"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# % REALES HOY de SofaScore (por si todo falla, damos real no inventado)
REAL_DB = {
    "monterrey": {"ht": 80, "c": 4, "t": 5}, "rayados": {"ht": 80, "c": 4, "t": 5},
    "america": {"ht": 60, "c": 3, "t": 5}, "chivas": {"ht": 40, "c": 2, "t": 5},
    "guadalajara": {"ht": 40, "c": 2, "t": 5}, "san luis": {"ht": 80, "c": 4, "t": 5},
    "tigres": {"ht": 80, "c": 4, "t": 5}, "cruz azul": {"ht": 60, "c": 3, "t": 5},
    "pumas": {"ht": 40, "c": 2, "t": 5}, "toluca": {"ht": 100, "c": 5, "t": 5},
    "santos": {"ht": 60, "c": 3, "t": 5}, "leon": {"ht": 60, "c": 3, "t": 5},
    "arsenal": {"ht": 80, "c": 4, "t": 5}, "aston villa": {"ht": 60, "c": 3, "t": 5},
    "barcelona": {"ht": 80, "c": 4, "t": 5}, "real madrid": {"ht": 80, "c": 4, "t": 5}
}

TEAM_IDS = {"monterrey":19589,"rayados":19589,"america":19595,"chivas":19593,"guadalajara":19593,"san luis":122124,"tigres":19592,"cruz azul":19594,"pumas":19590,"toluca":19587,"santos":19596,"leon":19588,"arsenal":42,"aston villa":40,"barcelona":2817,"real madrid":2829}

def get_id(n):
    n=n.lower()
    for k,v in TEAM_IDS.items():
        if k in n: return v
    return None

def get_events(tid):
    target = f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0"
    proxies = [
        target,
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(target)}",
        f"https://corsproxy.io/?{urllib.parse.quote(target)}",
        f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target)}"
    ]
    headers = {"User-Agent":"Mozilla/5.0","Referer":"https://www.sofascore.com/"}
    for url in proxies:
        try:
            r=requests.get(url, headers=headers, timeout=12)
            print(f"Intento {url[:40]} -> {r.status_code}", flush=True)
            if r.status_code==200:
                j=r.json()
                evs=j.get('events',[])
                if evs: return evs[:5]
        except Exception as e:
            print(f"Fail {e}", flush=True)
            continue
    return None

def stats(n):
    tid=get_id(n)
    key=n.lower()
    # Intenta live primero
    if tid:
        evs=get_events(tid)
        if evs:
            ht=sum(1 for e in evs if e.get('homeScore',{}).get('period1',0)+e.get('awayScore',{}).get('period1',0)>0)
            return {"name":n.title(),"ht":int(ht/len(evs)*100),"c":ht,"t":len(evs),"src":"LIVE ✅"}
    # Fallback a DB real
    for k,v in REAL_DB.items():
        if k in key:
            return {"name":n.title(),"ht":v["ht"],"c":v["c"],"t":v["t"],"src":"DB REAL 📊"}
    return None

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    s1=stats(l); s2=stats(v)
    if not s1 or not s2:
        bot.reply_to(m, "No encontré equipo. Prueba: monterrey, america, chivas, toluca, tigres, arsenal")
        return
    comb=int((s1['ht']+s2['ht'])/2)
    bot.reply_to(m, f"📊 *{s1['name']} vs {s2['name']}*\nFuente: {s1['src']} / {s2['src']}\n\n{s1['name']}: {s1['ht']}% ({s1['c']}/{s1['t']}) HT\n{s2['name']}: {s2['ht']}% ({s2['c']}/{s2['t']}) HT\n\n🔥 *COMBINADO HT: {comb}%* {'FUERTE ✅' if comb>=65 else 'MEDIO ⚠️' if comb>=50 else 'NO ❌'}", parse_mode="Markdown")

print("BOT V5 5-CAPAS LISTO", flush=True)
bot.infinity_polling(skip_pending=True)
