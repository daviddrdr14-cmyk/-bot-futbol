import os, time, pandas as pd, numpy as np, re, unicodedata
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V23.2"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

def clean(t):
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c)!= 'Mn')
    return t.lower().strip()

def get_stats(team, liga):
    try:
        team_c = clean(team)
        df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/"+liga+".csv")
        df['HomeTeam_c'] = df['HomeTeam'].apply(lambda x: clean(str(x)))
        df['AwayTeam_c'] = df['AwayTeam'].apply(lambda x: clean(str(x)))
        mask = df['HomeTeam_c'].str.contains(team_c, na=False)
        mask = mask | df['AwayTeam_c'].str.contains(team_c, na=False)
        df_t = df[mask].tail(5)
        if df_t.empty:
            mask2 = df['HomeTeam_c'].str.contains(team_c[:4], na=False)
            mask2 = mask2 | df['AwayTeam_c'].str.contains(team_c[:4], na=False)
            df_t = df[mask2].tail(5)
        if df_t.empty:
            df_t = df.tail(5)
        fd = team.title()
        tiros=[]
        sot=[]
        for _,r in df_t.iterrows():
            if team_c in r['HomeTeam_c']:
                tiros.append(r.get("HS",12))
                sot.append(r.get("HST",4))
            else:
                tiros.append(r.get("AS",11))
                sot.append(r.get("AST",3.5))
        ht = int(((df_t["HTHG"]+df_t["HTAG"])>0).mean()*100)
        o15 = int(((df_t["FTHG"]+df_t["FTAG"])>1.5).mean()*100)
        o25 = int(((df_t["FTHG"]+df_t["FTAG"])>2.5).mean()*100)
        btts = int(((df_t["FTHG"]>0)&(df_t["FTAG"]>0)).mean()*100)
        corn = round((df_t["HC"]+df_t["AC"]).mean(),1)
        corn_ht = round((df_t["HC"]+df_t["AC"]).mean()*0.45,1)
        cards = round((df_t["HY"]+df_t["AY"]).mean()+0.3,1)
        shots = round(float(np.mean(tiros)),1)
        soton = round(float(np.mean(sot)),1)
        return {"name":fd,"n":len(df_t),"liga":liga,"ht":ht,"o15":o15,"o25":o25,"btts":btts,"corn":corn,"corn_ht":corn_ht,"cards":cards,"shots":shots,"sot":soton}
    except:
        return None

def detect_liga(t):
    t=clean(t)
    if any(k in t for k in ["benfica","porto","sporting","braga","estoril","guimaraes"]): return "P1"
    if any(k in t for k in ["brugge","anderlecht","genk","antwerp","gent"]): return "B1"
    if any(k in t for k in ["ajax","psv","feyenoord","az","twente"]): return "N1"
    if any(k in t for k in ["galatasaray","fenerbahce","besiktas"]): return "T1"
    if any(k in t for k in ["olympi
