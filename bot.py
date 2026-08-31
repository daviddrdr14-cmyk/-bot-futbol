import os, time, requests
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot HT SofaScore Live!"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
bot.remove_webhook()
time.sleep(2)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def get_team_and_stats(nombre):
    # 1. Buscar equipo
    search = requests.get(f"https://api.sofascore.com/api/v1/search/all", params={"q": nombre}, headers=HEADERS, timeout=10).json()
    teams = [r for r in search.get('results', []) if r.get('type') == 'team']
    if not teams:
        return None, None
    team = teams[0]['entity']
    team_id = team['id']
    team_name = team['name']

    # 2. Últimos partidos
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"
    r = requests.get(url, headers=HEADERS, timeout=10).json()
    events = r.get('events', [])[:5]

    if not events:
        return team_name, None

    con_gol_ht = 0
    for ev in events:
        ht = ev.get('time', {}).get('halftime') or ev.get('halftimeScore')
        # Sofascore a veces lo manda en homeScore halftime
        try:
            h = ev['homeScore'].get('period1', 0)
            a = ev['awayScore'].get('period1', 0)
            if h + a > 0:
                con_gol_ht += 1
        except:
            pass

    prob = int((con_gol_ht / len(events)) * 100) if events else 0
    return team_name, {"prob": prob, "total": len(events), "con_gol": con_gol_ht}

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower():
        bot.reply_to(m, "Formato: Monterrey vs San Luis")
        return
    try:
        local_raw, visita_raw = [x.strip() for x in m.text.split("vs", 1)]
        bot.send_chat_action(m.chat.id, 'typing')

        name1, stats1 = get_team_and_stats(local_raw)
        name2, stats2 = get_team_and_stats(visita_raw)

        if not stats1 or not stats2:
            bot.reply_to(m, f"No encontré uno de los equipos. Intenta poner nombre completo: ej 'Monterrey' no 'Rayados'")
            return

        prob_final = int((stats1['prob'] + stats2['prob']) / 2)

        if prob_final >= 80: pick = "🔥 OVER 0.5 HT - ENTRADA FUERTE"; cuota = "1.35-1.50"
        elif prob_final >= 65: pick = "⚽ OVER 0.5 HT"; cuota = "1.55-1.75"
        else: pick = "❌ NO BET - Irse a Corners o esperar live min 20"; cuota = "1.90+"

        msg = f"""📊 *ANÁLISIS SOFASCORE REAL*

🏟️ *{name1} vs {name2}*

📈 {name1}: {stats1['con_gol']}/{stats1['total']} con gol HT ({stats1['prob']}%)
📈 {name2}: {stats2['con_gol']}/{stats2['total']} con gol HT ({stats2['prob']}%)

🔥 *Probabilidad Combinada Gol HT: {prob_final}%*

💰 *PICK: {pick}*
📊 Cuota estimada: {cuota}

_SofaScore Last 5 games - HT Period1_
"""
        bot.reply_to(m, msg, parse_mode="Markdown")
    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(m, f"Error SofaScore: {e} - Intenta con otro nombre")

print("BOT LISTO - SOFASCORE REAL")
bot.infinity_polling(skip_pending=True)
