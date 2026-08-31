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
def home(): return f"Bot V11 EURO+AMERICA Tiros - SD:{HAS_SD} LIVE"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# ========= MAPEO EQUIPOS FOOTBALL-DATA.CO.UK =========
TEAMS_FD = {
    # PREMIER E0
    "arsenal":"Arsenal","aston villa":"Aston Villa","man city":"Man City","manchester city":"Man City",
    "liverpool":"Liverpool","chelsea":"Chelsea","man united":"Man United","man utd":"Man United",
    "tottenham":"Tottenham","newcastle":"Newcastle","brighton":"Brighton","west ham":"West Ham",
    "crystal palace":"Crystal Palace","fulham":"Fulham","wolves":"Wolves","everton":"Everton",
    # LA LIGA SP1
    "real madrid":"Real Madrid","barcelona":"Barcelona","atletico":"Ath Madrid","atletico madrid":"Ath Madrid",
    "sevilla":"Sevilla","betis":"Betis","villarreal":"Villarreal","sociedad":"Real Sociedad","athletic":"Ath Bilbao",
    # SERIE A I1
    "inter":"Inter","milan":"AC Milan","juventus":"Juventus","napoli":"Napoli","roma":"Roma","lazio":"Lazio","atalanta":"Atalanta",
    # BUNDES D1
    "bayern":"Bayern Munich","dortmund":"Dortmund","leverkusen":"Leverkusen","leipzig":"RB Leipzig",
    # LIGUE 1 F1
    "psg":"Paris SG","marseille":"Marseille","lyon":"Lyon","lille":"Lille","monaco":"Monaco",
    # EREDIVISIE N1
    "ajax":"Ajax","psv":"PSV","feyenoord":"Feyenoord",
    # MLS - FBRef
    "inter miami":"Inter Miami","lafc":"Los Angeles FC","la galaxy":"LA Galaxy","columbus":"Columbus Crew",
    # LIGA MX - FBRef / MEX
    "america":"America","chivas":"Chivas","monterrey":"Monterrey","tigres":"Tigres UANL","cruz azul":"Cruz Azul","pumas":"Pumas","toluca":"Toluca","leon":"Leon","santos":"Santos Laguna","atlas":"Atlas",
    # BRAZIL B1
    "flamengo":"Flamengo","palmeiras":"Palmeiras","corinthians":"Corinthians","boca":"Boca Juniors","river":"River Plate"
}

# ========= DETECTA LIGA =========
def detect_league(text):
    t=text.lower()
    if any(x in t for x in ["madrid","barcelona","atletico","sevilla","betis","villarreal","sociedad","bilbao"]): return "SP1"
    if any(x in t for x in ["inter","milan","juve","napoli","roma","lazio","atalanta"]): return "I1"
    if any(x in t for x in ["bayern","dortmund","leverkusen","leipzig"]): return "D1"
    if any(x in t for x in ["psg","marseille","lyon","lille","monaco"]): return "F1"
    if any(x in t for x in ["ajax","psv","feyenoord"]): return "N1"
    if any(x in t for x in ["flamengo","palmeiras","corinthians"]): return "B1"
    if any(x in t for x in ["miami","lafc","galaxy","columbus"]): return "MLS"
    if any(x in t for x in ["america","chivas","monterrey","tigres","cruz azul","pumas","toluca"]): return "MEX"
    return "E0"

def get_football_data(team_key, league="E0"):
    team_fd = TEAMS_FD.get(team_key.lower().strip(), team_key.title().strip())
    try:
        # football-data solo tiene Europa bien. Para MLS/MEX usamos FBRef directo, aqui fallback a promedio
        if league in ["MLS","MEX","B1"]:
            # intenta leer igual, si no hay CSV usa promedio europeo
            url = f"https://www.football-data.co.uk/mmz4281/2526/{'E0' if league=='MLS' else league}.csv"
        else:
            url = f"https://www.football-data.co.uk/mmz4281/2526/{league}.csv"
        
        df = pd.read_csv(url)
        df_team = df[(df['HomeTeam']==team_fd) | (df['AwayTeam']==team_fd)].tail(5)
        if df_team.empty:
            df_team = df.tail(12) # promedio liga

        # Datos reales
        ht_gol = ((df_team['HTHG']+df_team['HTAG'])>0).mean()*100 if 'HTHG' in df_team.columns else 68
        over15 = ((df_team['FTHG']+df_team['FTAG'])>1.5).mean()*100 if 'FTHG' in df_team.columns else 75
        over25 = ((df_team['FTHG']+df_team['FTAG'])>2.5).mean()*100 if 'FTHG' in df_team.columns else 55
        btts = ((df_team['FTHG']>0) & (df_team['FTAG']>0)).mean()*100 if 'FTHG' in df_team.columns else 52
        corners = (df_team['HC']+df_team['AC']).mean() if 'HC' in df_team.columns else 9.5
        corners_ht = corners*0.45
        cards = (df_team['HY']+df_team['AY']+df_team['HR']*2+df_team['AR']*2).mean() if 'HY' in df_team.columns else 4.1
        shots = (df_team['HS']+df_team['AS']).mean()/2 if 'HS' in df_team.columns else 13.2
        sot = (df_team['HST']+df_team['AST']).mean()/2 if 'HST' in df_team.columns else 4.5
        wins = df_team.apply(lambda r: (r['HomeTeam']==team_fd and r['FTR']=='H') or (r['AwayTeam']==team_fd and r['FTR']=='A'), axis=1).sum()/len(df_team)*100
        draws = (df_team['FTR']=='D').mean()*100

        return {
            "name": team_fd, "t": len(df_team),
            "ht_gol": int(ht_gol), "over15": int(over15), "over25": int(over25), "btts": int(btts),
            "corners": round(float(corners),1), "corners_ht": round(float(corners_ht),1),
            "cards":
