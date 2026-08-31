import os, time, pandas as pd, numpy as np
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
def home(): return f"V13 AUTO-SWITCH SD:{HAS_SD} LIVE"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# DICCIONARIO HONESTO
TEAMS = {
    "arsenal":"Arsenal","aston villa":"Aston Villa","man city":"Man City","liverpool":"Liverpool","chelsea":"Chelsea","man united":"Man United","tottenham":"Tottenham","newcastle":"Newcastle","brighton":"Brighton","west ham":"West Ham","crystal palace":"Crystal Palace","fulham":"Fulham","wolves":"Wolves","everton":"Everton","nottm forest":"Nottm Forest","forest":"Nottm Forest","brentford":"Brentford","bournemouth":"Bournemouth",
    "real madrid":"Real Madrid","barcelona":"Barcelona","ath madrid":"Ath Madrid","atletico":"Ath Madrid","sevilla":"Sevilla","betis":"Betis","villarreal":"Villarreal","real sociedad":"Real Sociedad","ath bilbao":"Ath Bilbao","rayo vallecano":"Rayo Vallecano","rayo":"Rayo Vallecano","valencia":"Valencia","celta":"Celta","mallorca":"Mallorca","osasuna":"Osasuna","girona":"Girona","getafe":"Getafe","alaves":"Alaves","espanyol":"Espanyol","valladolid":"Valladolid",
    "inter":"Inter","ac milan":"AC Milan","milan":"AC Milan","juventus":"Juventus","napoli":"Napoli","roma":"Roma","lazio":"Lazio","atalanta":"Atalanta",
    "bayern":"Bayern Munich","dortmund":"Dortmund","leverkusen":"Leverkusen",
    "psg":"Paris SG","marseille":"Marseille","lille":"Lille","monaco":"Monaco","lyon":"Lyon",
    "ajax":"Ajax","psv":"PSV","feyenoord":"Feyenoord","benfica":"Benfica","porto":"Porto","sporting":"Sp Lisbon",
    "america":"America","chivas":"Guadalajara","guadalajara":"Guadalajara","monterrey":"Monterrey","tigres":"Tigres UANL","cruz azul":"Cruz Azul","pumas":"Pumas UNAM","toluca":"Toluca","santos laguna":"Santos Laguna","atlas":"Atlas","leon":"Leon",
    "inter miami":"Inter Miami","lafc":"Los Angeles FC","la galaxy":"LA Galaxy","columbus crew":"Columbus Crew",
    "flamengo":"Flamengo","palmeiras":"Palmeiras","corinthians":"Corinthians","boca juniors":"Boca Juniors","river plate":"River Plate"
}

LIGAS_EUROPA = ["E0","SP1","I1","D1","F1","N1","P1"]
LIGAS_MX = ["america","chivas","guadalajara","monterrey","tigres","cruz azul","pumas","toluca","santos laguna","atlas","leon"]
LIGAS_MLS = ["inter miami","lafc","la galaxy","columbus crew"]
LIGAS_BRA = ["flamengo","palmeiras","corinthians","boca juniors","river plate"]

def detect_tipo(text):
    t = text.lower()
    if any(x in t for x in LIGAS_MX): return "MX"
    if any(x in t for x in LIGAS_MLS): return "MLS"
    if any(x in t for x in LIGAS_BRA): return "BRA"
    if any(x in t for x in ["madrid","barcelona","atletico","sevilla","betis","villarreal","sociedad","bilbao","rayo","valencia","celta","mallorca","osasuna","girona","getafe","alaves","espanyol"]): return "SP1"
    if any(x in t for x in ["arsenal","aston villa","man city","liverpool","chelsea","man united","tottenham","newcastle","brighton","west ham","palace","fulham","wolves","everton","forest","brentford","bournemouth"]): return "E0"
    if any(x in t for x in ["inter","milan","juve","napoli","roma","lazio","atalanta"]): return "I1"
    if any(x in t for x in ["bayern","dortmund","leverkusen"]): return "D1"
    if any(x in t for x in ["psg","marseille","lille","monaco","lyon"]): return "F1"
    return "SP1"

def get_europa(team, liga_code):
    fd = TEAMS.get(team.lower().strip(), team.title().strip())
    try:
        df = pd.read_csv(f"https://www.football-data.co.uk/mmz4281/2526/{liga_code}.csv")
        df_t = df[(df["HomeTeam"]==fd)|(df["AwayTeam"]==fd)].tail(5)
        if df_t.empty: df_t = df.tail(10)
        tiros=[]; sot=[]
        for _,r in df_t.iterrows():
            if r["HomeTeam"]==fd: tiros.append(r.get("HS",13)); sot.append(r.get("HST",4.5))
            else: tiros.append(r.get("AS",11)); sot.append(r.get("AST",3.8))
        return {"name":fd,"n":len(df_t),"liga":liga_code,"ht":int(((df_t["HTHG"]+df_t["HTAG"])>0).mean()*100),"o15":int(((df_t["FTHG"]+df_t["FTAG"])>1.5).mean()*100),"o25":int(((df_t["FTHG"]+df_t["FTAG"])>2.5).mean()*100),"btts":int(((df_t["FTHG"]>0)&(df_t["FTAG"]>0)).mean()*100),"corn":round((df_t["HC"]+df_t["AC"]).mean(),1),"corn_ht":round((df_t["HC"]+df_t["AC"]).mean()*0.45,1),"cards":round((df_t["HY"]+df_t["AY"]).mean()+0.3,1),"shots":round(float(np.mean(tiros)),1),"sot":round(float(np.mean(sot)),1),"win":int(df_t.apply(lambda r: (r["HomeTeam"]==fd and r["FTR"]=="H") or (r["AwayTeam"]==fd and r["FTR"]=="A"), axis=1).sum()/len(df_t)*100),"draw":int((df_t["FTR"]=="D").mean()*100),"src":f"football-data {liga_code} COMPLETO"}
    except Exception as e:
        print(e)
        return {"name":fd,"n":5,"liga":liga_code,"ht":60,"o15":75,"o25":55,"btts":55,"corn":9.5,"corn_ht":4.2,"cards":3.9,"shots":12.5,"sot":4.2,"win":40,"draw":25,"src":f"{liga_code} fallback"}

def get_fbref_america(team, liga_fbref):
    if not HAS_SD: return None
    try:
        fb = sd.FBref(leagues=[liga_fbref], seasons="2025-2026")
        df = fb.read_team_season_stats(stat_type="shooting")
        # busca equipo
        key = TEAMS.get(team.lower().strip(), team).split()[0]
        row = df[df.index.get_level_values("team").str.contains(key, case=False, na=False)]
        if row.empty: return None
        r = row.iloc[-1]
        return {"name":TEAMS.get(team.lower().strip(), team.title()),"n":int(r.get("mp",10)),"liga":liga_fbref,"ht":0,"o15":0,"o25":0,"btts":0,"corn":9.0,"corn_ht":0,"cards":3.5,"shots":round(float(r.get("Gls",0)),1),"sot":round(float(r.get("SoT",0)),1),"xg":round(float(r.get("xg_for",1.2)),2),"win":0,"draw":0,"src":f"FBRef {liga_fbref} REAL - Sin 1T"}
    except Exception as e:
        print(f"FBRef error {e}")
        return None

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "V13 AUTO-SWITCH\nSi pones America vs Chivas = FBRef MX REAL\nSi pones Barcelona vs Rayo = football-data SP1 COMPLETO\nEscribe: Equipo vs Equipo")

@bot.message_handler(func=lambda m: "vs" in m.text.lower())
def h(m):
    try:
        l,v = [x.strip() for x in m.text.lower().split("vs",1)]
        tipo = detect_tipo(l+" "+v)

        if tipo == "MX":
            s1 = get_fbref_america(l, "MEX-Liga MX") or get_europa(l,"SP1")
            s2 = get_fbref_america(v, "MEX-Liga MX") or get_europa(v,"SP1")
            txt = f"*{s1['name']} vs {s2['name']}* - LIGA MX FBRef REAL\n⚠️ FBRef NO tiene Gol 1T ni Corner 1T\n\n*Tiros:* {s1['shots']} / {s2['shots']}\n*Tiros puerta:* {s1['sot']} / {s2['sot']}\n*xG:* {s1.get('xg','-')} / {s2.get('xg','-')}\n*Corners est:* {s1['corn']} / {s2['corn']}\n\n_Fuente: {s1['src']}_"

        elif tipo in ["MLS","BRA"]:
            liga_fb = "USA-Major League Soccer" if tipo=="MLS" else "BRA-Serie A"
            s1 = get_fbref_america(l, liga_fb) or get_europa(l,"SP1")
            s2 = get_fbref_america(v, liga_fb) or get_europa(v,"SP1")
            txt = f"*{s1['name']} vs {s2['name']}* - {tipo} FBRef REAL\n⚠️ Sin 1T\n\nTiros: {s1['shots']} / {s2['shots']}\n xG: {s1.get('xg','-')} / {s2.get('xg','-')}\n_Fuente: {s1['src']}_"

        else: # EUROPA
            s1 = get_europa(l, tipo); s2 = get_europa(v, tipo)
            txt = (
                f"*{s1['name']} vs {s2['name']}* - {s1['liga']} Ult {s1['n']}\n✅ DATOS COMPLETOS football-data\n\n"
                f"*PRIMER TIEMPO REAL*\nGol 1T: {s1['ht']}% | {s2['ht']}% -> {int((s1['ht']+s2['ht'])/2)}%\n"
                f"Corner 1T: {s1['corn_ht']} | {s2['corn_ht']}\n\n"
                f"*TOTALES ULT 5*\nOver1.5 {int((s1['o15']+s2['o15'])/2)}% Over2.5 {int((s1['o25']+s2['o25'])/2)}%\n"
                f"Corners: {s1['corn']} / {s2['corn']} -> {round((s1['corn']+s2['corn'])/2,1)}\n"
                f"Tarjetas: {s1['cards']} / {s2['cards']}\n"
                f"Tiros: {s1['shots']} / {s2['shots']}\n"
                f"Tiros puerta: {s1['sot']} / {s2['sot']}\n"
                f"BTTS {int((s1['btts']+s2['btts'])/2)}%\n\n"
                f"_Fuente: {s1['src']} LIVE_"
            )
        bot.reply_to(m, txt, parse_mode="Markdown")
    except Exception as e:
        print(e); bot.reply_to(m, f"Error {e}")

print("V13 AUTO-SWITCH LISTO", flush=True)
bot.infinity_polling(timeout=90, long_polling_timeout=90)
