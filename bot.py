import os, time, requests
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot FIX!"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
bot.remove_webhook()
time.sleep(2)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Accept": "application/json, text/plain, */*"
}

# MAPA DIRECTO PARA QUE NO FALLE - Agrega los que uses
TEAMS_MAP = {
    "monterrey": 19589, "rayados": 19589,
    "san luis": 122124, "atletico san luis": 122124,
    "america": 19595, "club america": 19595,
    "chivas": 19593, "guadalajara": 19593,
    "tigres": 19592, "cruz azul": 19594,
    "aston villa": 40, "arsenal": 42,
    "man city": 17, "manchester city": 17,
    "liverpool": 44, "chelsea": 38, "barcelona": 2817, "real madrid": 2829
}

def get_stats(nombre):
    nombre_low = nombre.lower().strip()
    team_id = TEAMS_MAP.get(nombre_low)
    team_name = nombre.title()

    if not team_id:
        try:
            # Intento 1: Buscador
            s = requests.get("https://api.sofascore.com/api/v1/search/all", params={"q": nombre}, headers=HEADERS, timeout=15).json()
            results = s.get('results', [])
            print(f"SEARCH {nombre}: {results[:1]}")
            for r in results:
                if r.get('type') == 'team':
                    team_id = r['entity']['id']
                    team_name = r['entity']['name']
                    break
            if not team_id:
                # Intento 2: endpoint teams
                s2 = requests.get(f"https://api.sofascore.com/api/v1/search/teams", params={"q": nombre}, headers=HEADERS, timeout=15).json()
                if s2.get('results'):
                    team_id = s2['results'][0]['entity']['id']
                    team_name = s2['results'][0]['entity']['name']
        except Exception as e:
            print("SEARCH ERROR:", e)

    if not team_id:
        return None

    try:
        ev = requests.get(f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0", headers=HEADERS, timeout=15).json()
        events = ev.get('events', [])[:5]
        if not events: return None
        ht = btts = o15 = o25 = 0
        for e in events:
            h1 = e['homeScore'].get('period1',0); a1 = e['awayScore'].get('period1',0)
            h = e['homeScore'].get('current',0); a = e['awayScore'].get('current',0)
            if h1+a1>0: ht+=1
            if h>=1 and a>=1: btts+=1
            if h+a>=2: o15+=1
            if h+a>=3: o25+=1
        n = len(events)
        return {"name": team_name, "ht": int(ht/n*100), "btts": int(btts/n*100), "o15": int(o15/n*100), "o25": int(o25/n*100), "n": n, "ht_c": ht}
    except Exception as e:
        print("EVENTS ERROR:", e)
        return None

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l_raw, v_raw = [x.strip() for x in m.text.split("vs",1)]
    bot.send_chat_action(m.chat.id, 'typing')
    s1 = get_stats(l_raw)
    s2 = get_stats(v_raw)
    if not s1 or not s2:
        bot.reply_to(m, f"No jalo el ID. Mándame log de Render. Intenté: {l_raw} y {v_raw}")
        return
    ht = int((s1['ht']+s2['ht'])/2)
    bot.reply_to(m, f"""📊 *{s1['name']} vs {s2['name']} - REAL*

HT: {s1['ht']}% ({s1['ht_c']}/{s1['n']}) | {s2['ht']}%
🔥 *COMBINADO HT: {ht}%* - {'FUERTE ✅' if ht>=70 else 'MEDIO' if ht>=55 else 'NO ❌'}

Over 1.5: {int((s1['o15']+s2['o15'])/2)}% | BTTS: {int((s1['btts']+s2['btts'])/2)}%

PICK: {'OVER 0.5 HT' if ht>=65 else 'ESPERAR LIVE'}
""", parse_mode="Markdown")

print("BOT FIX LISTO")
bot.infinity_polling(skip_pending=True)
