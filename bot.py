import os, time, requests
from flask import Flask
from threading import Thread
import telebot

print("=== INICIANDO ===")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot OK"

def run_flask():
    print("FLASK INICIANDO EN 10000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

Thread(target=run_flask, daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN EXISTE: {bool(TOKEN)} - {TOKEN[:10] if TOKEN else 'NO'}...")

if not TOKEN:
    print("ERROR: NO HAY BOT_TOKEN EN RENDER")
else:
    try:
        bot = telebot.TeleBot(TOKEN)
        bot.remove_webhook()
        print("WEBHOOK REMOVIDO")
        time.sleep(2)

        HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.sofascore.com/"}
        TEAMS_MAP = {"monterrey":19589,"san luis":122124,"america":19595,"chivas":19593,"aston villa":40,"arsenal":42,"man city":17,"liverpool":44,"barcelona":2817,"real madrid":2829}

        def get_stats(nombre):
            nid = TEAMS_MAP.get(nombre.lower().strip())
            if not nid: return None
            ev = requests.get(f"https://api.sofascore.com/api/v1/team/{nid}/events/last/0", headers=HEADERS, timeout=15).json()
            events = ev.get('events', [])[:5]
            ht = sum(1 for e in events if e['homeScore'].get('period1',0)+e['awayScore'].get('period1',0)>0)
            return {"name": nombre.title(), "ht": int(ht/len(events)*100) if events else 0}

        @bot.message_handler(func=lambda m: True)
        def h(m):
            if "vs" not in m.text.lower(): return
            l,v = [x.strip() for x in m.text.split("vs",1)]
            s1=get_stats(l); s2=get_stats(v)
            if not s1 or not s2: bot.reply_to(m, "Equipo no en mapa, usa: monterrey, america, arsenal, etc"); return
            ht=int((s1['ht']+s2['ht'])/2)
            bot.reply_to(m, f"HT {s1['name']} {s1['ht']}% + {s2['name']} {s2['ht']}% = *{ht}%* {'FUERTE ✅' if ht>=70 else 'NO'}", parse_mode="Markdown")

        print("BOT FIX LISTO - INICIANDO POLLING")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"ERROR FATAL BOT: {e}")
        import traceback; traceback.print_exc()
        time.sleep(999999)
