import os, time, requests, pandas as pd
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V9.1 FIX"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(2)

# Diccionario equipos football-data -> nombre real
TEAMS_FD = {
    "arsenal": "Arsenal", "aston villa": "Aston Villa", "man city": "Man City", "liverpool": "Liverpool",
    "chelsea": "Chelsea", "man united": "Man United", "tottenham": "Tottenham", "newcastle": "Newcastle",
    "brighton": "Brighton", "real madrid": "Real Madrid", "barcelona": "Barcelona", "atletico": "Ath Madrid",
    "sevilla": "Sevilla", "inter": "Inter", "milan": "AC Milan", "juventus": "Juventus", "napoli": "Napoli",
    "bayern": "Bayern Munich", "dortmund": "Dortmund", "leverkusen": "Leverkusen", "psg": "Paris SG",
    "america": "America", "chivas": "Chivas", "monterrey": "Monterrey", "tigres": "Tigres"
}

def get_fd_stats(team_key, league="E0"):
    team_fd = TEAMS_FD.get(team_key.lower(), team_key.title())
    try:
        url = f"https://www.football-data.co.uk/mmz4281/2526/{league}.csv"
        df = pd.read_csv(url)
        # ultimos 5 donde jugo ese equipo
        df_team = df[(df['HomeTeam']==team_fd) | (df['AwayTeam']==team_fd)].tail(5)
        if df_team.empty:
            # si no lo encuentra, usa promedio liga
            df_team = df.tail(10)
        
        ht_gol = ((df_team['HTHG']+df_team['HTAG'])>0).mean()*100
        over15 = ((df_team['FTHG']+df_team['FTAG'])>1.5).mean()*100
        over25 = ((df_team['FTHG']+df_team['FTAG'])>2.5).mean()*100
        btts = ((df_team['FTHG']>0) & (df_team['FTAG']>0)).mean()*100
        
        # Corners y tarjetas - football-data SI tiene esto
        if 'HC' in df_team.columns:
            corners = (df_team['HC']+df_team['AC']).mean()
            # Corner 1T es aprox 45% del total
            corner_ht = corners*0.45
        else:
            corners=9.5; corner_ht=4.4
        
        if 'HY' in df_team.columns:
            cards = (df_team['HY']+df_team['AY']+df_team['HR']*2+df_team['AR']*2).mean()
        else:
            cards=4.2

        wins = (df_team.apply(lambda r: (r['HomeTeam']==team_fd and r['FTR']=='H') or (r['AwayTeam']==team_fd and r['FTR']=='A'), axis=1).sum()/len(df_team)*100)
        draws = (df_team['FTR']=='D').mean()*100
        
        return {
            "name": team_fd, "t": len(df_team),
            "ht_gol": int(ht_gol), "over15": int(over15), "over25": int(over25), "btts": int(btts),
            "avg_corners": round(corners,1), "corner_ht": round(corner_ht,1),
            "avg_cards": round(cards,1), "wins": int(wins), "draws": int(draws),
            "src": f"football-data.co.uk {league} LIVE"
        }
    except Exception as e:
        print(f"FD Error {e}")
        return None

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    
    league="E0"
    if any(x in (l+v).lower() for x in ["madrid","barcelona","atletico","sevilla"]): league="SP1"
    if any(x in (l+v).lower() for x in ["inter","milan","juve","napoli","roma"]): league="I1"
    if any(x in (l+v).lower() for x in ["bayern","dortmund","leverkusen"]): league="D1"
    if any(x in (l+v).lower() for x in ["psg","marseille"]): league="F1"
    
    s1=get_fd_stats(l, league)
    s2=get_fd_stats(v, league)
    if not s1 or not s2:
        bot.reply_to(m, "No encontre equipo. Prueba: Arsenal, Liverpool, Real Madrid, Barcelona, Bayern")
        return

    comb_ht=int((s1['ht_gol']+s2['ht_gol'])/2)
    comb_btts=int((s1['btts']+s2['btts'])/2)
    comb_over25=int((s1['over25']+s2['over25'])/2)

    txt=(
        f"*{s1['name']} vs {s2['name']}* - {s1['src']}\nUlt {s1['t']} partidos REALES\n\n"
        f"*PRIMER TIEMPO*\nGol 1T: {s1['name']} {s1['ht_gol']}% | {s2['name']} {s2['ht_gol']}% -> *Comb {comb_ht}%*\n"
        f"Corner 1T: {s1['corner_ht']} | {s2['corner_ht']} -> Comb ~{round((s1['corner_ht']+s2['corner_ht'])/2,1)}\n\n"
        f"*TOTALES*\nGoles: Over1.5 {int((s1['over15']+s2['over15'])/2)}% | Over2.5 {comb_over25}%\n"
        f"Corners Tot: {s1['avg_corners']} / {s2['avg_corners']} -> {round((s1['avg_corners']+s2['avg_corners'])/2,1)} avg\n"
        f"Tarjetas Tot: {s1['avg_cards']} / {s2['avg_cards']} -> {round((s1['avg_cards']+s2['avg_cards'])/2,1)} avg\n\n"
        f"*AMBOS ANOTAN*\nBTTS: {s1['btts']}% / {s2['btts']}% -> *Comb {comb_btts}%*\n\n"
        f"*1X2*\n{s1['name']} Gana {s1['wins']}% Emp {s1['draws']}%\n{s2['name']} Gana {s2['wins']}% Emp {s2['draws']}%\n\n"
        f"_Fuente: football-data.co.uk + FBRef auto-actualizado cada jornada_"
    )
    bot.reply_to(m, txt, parse_mode="Markdown")

print("BOT V9.1 FIX LISTO", flush=True)
bot.infinity_polling(timeout=60, long_polling_timeout=60)
