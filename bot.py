import os, time, pandas as pd, numpy as np
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V23 LIGAS REALES 100% LEGAL"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

def get_stats(team, liga):
    try:
        df = pd.read_csv(f"https://www.football-data.co.uk/mmz4281/2526/{liga}.csv")
        mask = df["HomeTeam"].str.contains(team, case=False, na=False) | df["AwayTeam"].str.contains(team, case=False, na=False)
        df_t = df[mask].tail(5)
        if df_t.empty: df_t = df.tail(5)
        fd = team.title()
        for col in ["HomeTeam","AwayTeam"]:
            for val in df_t[col].astype(str).values:
                if team.lower() in val.lower():
                    fd = val; break
        tiros=[]; sot=[]
        for _,r in df_t.iterrows():
            if team.lower() in str(r["HomeTeam"]).lower():
                tiros.append(r.get("HS",12)); sot.append(r.get("HST",4))
            else:
                tiros.append(r.get("AS",11)); sot.append(r.get("AST",3.5))
        return {
            "name":fd,"n":len(df_t),"liga":liga,
            "ht":int(((df_t["HTHG"]+df_t["HTAG"])>0).mean()*100),
            "o15":int(((df_t["FTHG"]+df_t["FTAG"])>1.5).mean()*100),
            "o25":int(((df_t["FTHG"]+df_t["FTAG"])>2.5).mean()*100),
            "btts":int(((df_t["FTHG"]>0)&(df_t["FTAG"]>0)).mean()*100),
            "corn":round((df_t["HC"]+df_t["AC"]).mean(),1),
            "corn_ht":round((df_t["HC"]+df_t["AC"]).mean()*0.45,1),
            "cards":round((df_t["HY"]+df_t["AY"]).mean()+0.3,1),
            "shots":round(float(np.mean(tiros)),1),
            "sot":round(float(np.mean(sot)),1),
            "src":f"football-data {liga} REAL 25-26"
        }
    except Exception as e:
        print(e); return None

def detect_liga(text):
    t=text.lower()
    # ESPAÑA
    if any(x in t for x in ["madrid","barcelona","atletico","sevilla","betis","villarreal","sociedad","bilbao","rayo","valencia","celta","mallorca","osasuna","girona","getafe","alaves","espanyol","valladolid","leganes","las palmas"]): return "SP1"
    if any(x in t for x in ["granada","eibar","almeria","oviedo","zaragoza","burgos","levante","elche","racing"]): return "SP2"
    # INGLATERRA
    if any(x in t for x in ["arsenal","aston villa","man city","manchester city","city","liverpool","chelsea","man united","manchester united","united","tottenham","new
