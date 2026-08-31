import os, time, requests, pandas as pd
from flask import Flask
from threading import Thread
import telebot

try:
    import soccerdata as sd
    HAS_SD = True
except:
    HAS_SD = False

app = Flask(__name__)
@app.route('/')
def home(): return f"Bot V10 COMPLETA - SD:{HAS_SD}"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(2)

TEAMS_FD = {
    "arsenal": "Arsenal", "aston villa": "Aston Villa", "man city": "Man City", "manchester city": "Man City",
    "liverpool": "Liverpool", "chelsea": "Chelsea", "man united": "Man United", "man utd": "Man United",
    "tottenham": "Tottenham", "newcastle": "Newcastle", "brighton": "Brighton", "west ham": "West Ham",
    "real madrid": "Real Madrid", "barcelona": "Barcelona", "atletico": "Ath Madrid", "atletico madrid": "Ath Madrid",
    "sevilla": "Sevilla", "betis": "Betis", "inter": "Inter", "milan": "AC Milan", "juventus": "Juventus",
    "napoli": "Napoli", "roma": "Roma", "bayern": "Bayern Munich", "dortmund": "Dortmund",
    "leverkusen": "Leverkusen", "psg": "Paris SG"
}

def get_football_data(team_key, league="E0"):
    team_fd = TEAMS_FD.get(team_key.lower(), team_key.title())
    try:
        url = f"https://www.football-data.co.uk/mmz4281/2526/{league}.csv"
        df = pd.read_csv(url)
        df_team = df[(df['HomeTeam']==team_fd) | (df['AwayTeam']==team_fd)].tail(5)
        if df_team.empty: df_team = df.tail(10)
        
        return {
            "name": team_fd,
            "t": len(df_team),
            "ht_gol": int(((df_team['HTHG']+df_team['HTAG'])>0).mean()*100),
            "over15": int(((df_team['FTHG']+df_team['FTAG'])>1.5).mean()*100),
            "over25": int(((df_team['FTHG']+df_team['FTAG'])>2.5).mean()*100),
            "btts": int(((df_team['FTHG']>0) & (df_team['FTAG']>0)).mean()*100),
            "corners": round((df_team['HC']+df_team['AC']).mean(),1) if 'HC' in df_team.columns else 9.5,
            "corners_ht": round((df_team['HC']+df_team['AC']).mean()*0.45,1),
            "cards": round((df_team['HY']+df_team['AY']+df_team['HR']*2+df_team['AR']*2).mean(),1) if 'HY' in df_team.columns else 4.2,
            "wins": int(df_team.apply(lambda r: (r['HomeTeam']==team_fd and r['FTR']=='H') or (r['AwayTeam']==team_fd and r['FTR']=='A'), axis=1).sum()/len(df_team)*100),
            "draws": int((df_team['FTR']=='D').mean()*100)
        }
    except Exception as e:
        print(f"FD err {e}")
        return None

def get_fbref_advanced(team_name):
    if not HAS_SD: return None
    try:
        # FBRef: busca en Premier primero, luego LaLiga, etc
        fb = sd.FBref(leagues=["ENG-Premier League","ESP-La Liga","ITA-Serie A","GER-Bundesliga","FRA-Ligue 1"], seasons="2025-2026")
        # shooting = xG, xGA, tiros a puerta
        shoot = fb.read_team_season_stats(stat_type="shooting")
        poss = fb.read_team_season_stats(stat_type="possession")
        
        # busca equipo
        team_row_s = shoot[shoot.index.get_level_values('team').str.contains(team_name, case=False, na=False)]
        team_row_p = poss[poss.index.get_level_values('team').str.contains(team_name, case=False, na=False)]
        
        if team_row_s.empty: return None
        
        last = team_row_s.iloc[-1]
        last_p = team_row_p.iloc[-1] if not team_row_p.empty else None
        
        return {
            "xg": round(float(last.get('xg_for', 0)),2),
            "xga": round(float(last.get('xg_against', 0)),2),
            "sot": round(float(last.get('sot_for', 0)),1),
            "poss": int(last_p.get('poss', 50)) if last_p is not None else 50
        }
    except Exception as e:
        print(f"FBRef adv err {e}")
        return None

@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "Escribe: Equipo vs Equipo\nEj: Arsenal vs Aston Villa")

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    league="E0"
    if any(x in (l+v).lower() for x in ["madrid","barcelona","atletico","sevilla","betis"]): league="SP1"
    if any(x in (l+v).lower() for x in ["inter","milan","juve","napoli","roma"]): league="I1"
    if any(x in (l+v).lower() for x in ["bayern","dortmund","leverkusen"]): league="D1"
    if any(x in (l+v).lower() for x in ["psg"]): league="F1"

    s1=get_football_data(l, league)
    s2=get_football_data(v, league)
    if not s1 or not s2:
        bot.reply_to(m, "Equipo no encontrado. Prueba con Arsenal, Man City, Real Madrid, Barcelona, Bayern, PSG")
        return

    fb1=get_fbref_advanced(l)
    fb2=get_fbref_advanced(v)

    comb_ht=int((s1['ht_gol']+s2['ht_gol'])/2)
    comb_btts=int((s1['btts']+s2['btts'])/2)
    comb_over25=int((s1['over25']+s2['over25'])/2)
    comb_corners=round((s1['corners']+s2['corners'])/2,1)
    comb_cards=round((s1['cards']+s2['cards'])/2,1)

    # Texto FBRef si existe
    fb_text=""
    if fb1 and fb2:
        fb_text=f"\n*DATOS AVANZADOS FBREF*\n{s1['name']}: xG {fb1['xg']} | xGA {fb1['xga']} | Tiros puerta {fb1['sot']} | Pos {fb1['poss']}%\n{s2['name']}: xG {fb2['xg']} | xGA {fb2['xga']} | Tiros puerta {fb2['sot']} | Pos {fb2['poss']}%\n"

    txt=(
        f"*{s1['name']} vs {s2['name']}* - Ult {s1['t']} partidos\n\n"
        f"*PRIMER TIEMPO*\nGol 1T: {s1['ht_gol']}% | {s2['ht_gol']}% -> *Comb {comb_ht}%*\nCorner 1T: {s1['corners_ht']} | {s2['corners_ht']} -> ~{round((s1['corners_ht']+s2['corners_ht'])/2,1)}\n\n"
        f"*TOTALES*\nOver1.5 {int((s1['over15']+s2['over15'])/2)}% | Over2.5 {comb_over25}%\nCorners: {s1['corners']} / {s2['corners']} -> *{comb_corners} avg*\nTarjetas: {s1['cards']} / {s2['cards']} -> *{comb_cards} avg*\n\n"
        f"*AMBOS ANOTAN*\nBTTS {s1['btts']}% / {s2['btts']}% -> *{comb_btts}%*\n\n"
        f"*1X2*\n{s1['name']} Gana {s1['wins']}% Emp {s1['draws']}%\n{s2['name']} Gana {s2['wins']}% Emp {s2['draws']}%\n"
        f"{fb_text}\n"
        f"_Fuente: football-data.co.uk + FBRef (soccerdata) - Auto actualizado_"
    )
    bot.reply_to(m, txt, parse_mode="Markdown")

print("BOT V10 COMPLETA LISTO", flush=True)
bot.infinity_polling(timeout=60, long_polling_timeout=60)
