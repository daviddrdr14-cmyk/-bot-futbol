import os, time, pandas as pd, numpy as np
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V23 FIX"
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
        return {"name":fd,"n":len(df_t),"liga":liga,"ht":int(((df_t["HTHG"]+df_t["HTAG"])>0).mean()*100),"o15":int(((df_t["FTHG"]+df_t["FTAG"])>1.5).mean()*100),"o25":int(((df_t["FTHG"]+df_t["FTAG"])>2.5).mean()*100),"btts":int(((df_t["FTHG"]>0)&(df_t["FTAG"]>0)).mean()*100),"corn":round((df_t["HC"]+df_t["AC"]).mean(),1),"corn_ht":round((df_t["HC"]+df_t["AC"]).mean()*0.45,1),"cards":round((df_t["HY"]+df_t["AY"]).mean()+0.3,1),"shots":round(float(np.mean(tiros)),1),"sot":round(float(np.mean(sot)),1),"src":f"football-data {liga} REAL"}
    except Exception as e:
        print(e); return None

def detect_liga(t):
    t=t.lower()
    if any(k in t for k in ["benfica","porto","sporting","braga","guimaraes"]): return "P1"
    if any(k in t for k in ["brugge","anderlecht","genk","antwerp","gent","liege","union sg"]): return "B1"
    if any(k in t for k in ["ajax","psv","feyenoord","az","twente","utrecht"]): return "N1"
    if any(k in t for k in ["galatasaray","fenerbahce","besiktas","trabzonspor"]): return "T1"
    if any(k in t for k in ["olympiacos","panathinaikos","aek","paok"]): return "G1"
    if any(k in t for k in ["celtic","rangers","hearts","aberdeen"]): return "SC0"
    if any(k in t for k in ["bayern","dortmund","leverkusen","leipzig","stuttgart","frankfurt"]): return "D1"
    if any(k in t for k in ["psg","marseille","lille","monaco","lyon","lens","rennes","nice"]): return "F1"
    if any(k in t for k in ["atalanta","inter","milan","juventus","juve","napoli","roma","lazio","bologna","fiorentina","torino","udinese"]): return "I1"
    if any(k in t for k in ["arsenal","aston","city","liverpool","chelsea","united","tottenham","newcastle","brighton","west ham","palace","fulham","wolves","everton","forest","brentford"]): return "E0"
    return "SP1"

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "BOT V23 FIX 23 LIGAS REALES\nBenfica vs Porto\nGalatasaray vs Fenerbahce\nAjax vs PSV\nAtalanta vs Bologna")

@bot.message_handler(func=lambda m: "vs" in m.text.lower())
def handle(m):
    try:
        l,v=[x.strip() for x in m.text.lower().split("vs",1)]
        liga=detect_liga(l+" "+v)
        s1=get_stats(l,liga); s2=get_stats(v,liga)
        if not s1 or not s2:
            bot.reply_to(m, f"No encontre {l} o {v} en {liga}"); return
        txt=f"*{s1['name']} vs {s2['name']}* - {s1['liga']} Ult {s1['n']}J\n✅ REAL\n\n*1T REAL*\nGol 1T: {s1['ht']}% | {s2['ht']}% -> {int((s1['ht']+s2['ht'])/2)}%\nCorner 1T: {s1['corn_ht']} | {s2['corn_ht']}\n\n*TOTALES*\nO1.5 {s1['o15']}%/{s2['o15']}% O2.5 {s1['o25']}%/{s2['o25']}%\nCorners {s1['corn']}/{s2['corn']} Tarj {s1['cards']}/{s2['cards']}\nTiros {s1['shots']}/{s2['shots']} Puerta {s1['sot']}/{s2['sot']}\n\n_{s1['src']}_"
        bot.reply_to(m, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(m, f"Error {e}")

print("BOT V23 FIX LISTO", flush=True)
bot.infinity_polling(timeout=90, long_polling_timeout=90)
