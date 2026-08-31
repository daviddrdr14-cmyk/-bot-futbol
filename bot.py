import os, time, requests
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot HT V3 AntiBloqueo"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

TEAMS = {"monterrey":19589,"rayados":19589,"san luis":122124,"america":19595,"chivas":19593,"guadalajara":19593,"tigres":19592,"cruz azul":19594,"pumas":19590,"arsenal":42,"barcelona":2817,"real madrid":2829}

def get_id(n):
    n=n.lower()
    for k,v in TEAMS.items():
        if k in n: return v
    return None

def get_events(tid):
    urls = [
        f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0",
        f"https://www.sofascore.com/api/v1/team/{tid}/events/last/0",
        f"https://api.sofascore.app/api/v1/team/{tid}/events/last/0"
    ]
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Referer":"https://www.sofascore.com/","Accept":"*/*"}
    for url in urls:
        try:
            r=requests.get(url, headers=headers, timeout=12)
            if r.status_code==200 and 'events' in r.text:
                print(f"OK {tid} con {url}", flush=True)
                return r.json().get('events',[])[:5]
            else:
                print(f"FAIL {tid} {url} -> {r.status_code}", flush=True)
        except Exception as e:
            print(f"ERR url {e}", flush=True)
    return None

def stats(n):
    tid=get_id(n)
    if not tid: return None
    evs=get_events(tid)
    if not evs: return None
    ht=sum(1 for e in evs if e.get('homeScore',{}).get('period1',0)+e.get('awayScore',{}).get('period1',0)>0)
    return {"name":n.title(),"ht":int(ht/len(evs)*100),"c":ht,"t":len(evs)}

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    print(f"RECIBIDO V3: {l} vs {v}", flush=True)
    s1=stats(l); s2=stats(v)
    if not s1 or not s2:
        # Fallback para no dejarte sin respuesta si SofaScore bloquea total
        if not s1: s1={"name":l.title(),"ht":65,"c":3,"t":5}
        if not s2: s2={"name":v.title(),"ht":65,"c":3,"t":5}
        bot.reply_to(m, f"⚠️ SofaScore bloqueando IP de Render, usando estimado alto\n\n📊 *{s1['name']} vs {s2['name']}*\n\n{s1['name']}: {s1['ht']}% HT\n{s2['name']}: {s2['ht']}% HT\n\n🔥 *COMBINADO: {int((s1['ht']+s2['ht'])/2)}% MEDIO* (modo anti-bloqueo)", parse_mode="Markdown")
        return
    comb=int((s1['ht']+s2['ht'])/2)
    bot.reply_to(m, f"📊 *{s1['name']} vs {s2['name']} - REAL*\n\n{s1['name']}: {s1['ht']}% ({s1['c']}/{s1['t']})\n{s2['name']}: {s2['ht']}% ({s2['c']}/{s2['t']})\n\n🔥 *COMBINADO HT: {comb}%* {'FUERTE ✅' if comb>=65 else 'MEDIO ⚠️' if comb>=50 else 'NO ❌'}", parse_mode="Markdown")

print("BOT V3 ANTI-BLOQUEO LISTO", flush=True)
bot.infinity_polling(skip_pending=True)
