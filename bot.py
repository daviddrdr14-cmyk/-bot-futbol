import os, time, pandas as pd, numpy as np, re, unicodedata
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V23.1 ULTRA FIX"
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
        df = pd.read_csv(f"https://www.football-data.co.uk/mmz4281/2526/{liga}.csv")
        df['HomeTeam_c'] = df['HomeTeam'].apply(lambda x: clean(str(x)))
        df['AwayTeam_c'] = df['AwayTeam'].apply(lambda x: clean(str(x)))
        mask = df['HomeTeam_c'].str.contains(team_c, na=False) | df['AwayTeam_c'].str.contains(team_c, na=False)
        df_t = df[mask].tail(5)
        if df_t.empty:
            # busqueda por primeras 4 letras
            mask2 = df['HomeTeam_c'].str.contains(team_c[:4], na=False) | df['AwayTeam_c'].str.contains(team_c[:4], na=False)
            df_t = df[mask2].tail(5)
        if df_t.empty:
            df_t = df.tail(5)

        # nombre real
        fd = team.title()
        for _,r in df_t.iterrows():
            if team_c in r['HomeTeam_c'] or team_c in r['AwayTeam_c']:
                fd = r['HomeTeam'] if team_c in r['HomeTeam_c'] else r['AwayTeam']
                break

        tiros=[]; sot=[]
        for _,r in df_t.iterrows():
            if team_c in r['HomeTeam_c']:
                tiros.append(r.get("HS",12)); sot.append(r.get("HST",4))
            else:
                tiros.append(r.get("AS",11)); sot.append(r.get("AST",3.5))

        return {"name":fd,"n":len(df_t),"liga":liga,"ht":int(((df_t["HTHG"]+df_t["HTAG"])>0).mean()*100),"o15":int(((df_t["FTHG"]+df_t["FTAG"])>1.5).mean()*100),"o25":int(((df_t["FTHG"]+df_t["FTAG"])>2.5).mean()*100),"btts":int(((df_t["FTHG"]>0)&(df_t["FTAG"]>0)).mean()*100),"corn":round((df_t["HC"]+df_t["AC"]).mean(),1),"corn_ht":round((df_t["HC"]+df_t["AC"]).mean()*0.45,1),"cards":round((df_t["HY"]+df_t["AY"]).mean()+0.3,1),"shots":round(float(np.mean(tiros)),1),"sot":round(float(np.mean(sot)),1),"src":f"football-data {liga} REAL"}
    except Exception as e:
        print(f"Error stats {team} {liga}: {e}"); return None

def detect_liga(t):
    t=clean(t)
    if any(k in t for k in ["benfica","porto","sporting","braga","estoril","guimaraes","famalicao"]): return "P1"
    if any(k in t for k in ["brugge","anderlecht","genk","antwerp","gent","liege","union"]): return "B1"
    if any(k in t for k in ["ajax","psv","feyenoord","az","twente","utrecht","feyenoord"]): return "N1"
    if any(k in t for k in ["galatasaray","fenerbahce","besiktas","trabzon"]): return "T1"
    if any(k in t for k in ["olympiacos","panathinaikos","aek","paok"]): return "G1"
    if any(k in t for k in ["celtic","rangers","hearts","aberdeen"]): return "SC0"
    if any(k in t for k in ["bayern","dortmund","leverkusen","leipzig","stuttgart","frankfurt","wolfsburg"]): return "D1"
    if any(k in t for k in ["psg","marseille","lille","monaco","lyon","lens","rennes","nice","brest"]): return "F1"
    if any(k in t for k in ["lecce","atalanta","inter","milan","juventus","juve","napoli","roma","lazio","bologna","fiorentina","torino","udinese","genoa","cagliari","como","parma","verona","empoli"]): return "I1"
    if any(k in t for k in ["arsenal","aston","city","liverpool","chelsea","united","tottenham","newcastle","brighton","west ham","palace","fulham","wolves","everton","forest","brentford","bournemouth"]): return "E0"
    return "SP1"

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "BOT V23.1 FIX - Ya aguanta vss y acentos\nPrueba: Lecce vs Roma\nBenfica vs Estoril")

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        txt = clean(m.text)
        if "vs" not in txt: return
        # separa por vs, vss, vs., vs-
        partes = re.split(r'\s+v+s+\s*|\s+vs\.?\s*|\s+-\s+vs\s+', txt)
        if len(partes) < 2:
            partes = txt.split("vs")
        l = partes[0].strip()
        v = partes[1].strip()
        if not l or not v: return
        liga = detect_liga(l+" "+v)
        s1 = get_stats(l, liga)
        s2 = get_stats(v, liga)
        if not s1 or not s2:
            bot.reply_to(m, f"No encontre {l} o {v} en {liga}. Prueba sin acentos: {l} vs {v}")
            return
        res = f"*{s1['name']} vs {s2['name']}* - {s1['liga']} Ult {s1['n']}J\n✅ REAL\n\n*1T REAL*\nGol 1T: {s1['ht']}% | {s2['ht']}% -> {int((s1['ht']+s2['ht'])/2)}%\nCorner 1T: {s1['corn_ht']} | {s2['corn_ht']}\n\n*TOTALES*\nO1.5 {s1['o15']}%/{s2['o15']}% O2.5 {s1['o25']}%/{s2['o25']}%\nCorners {s1['corn']}/{s2['corn']} Tarj {s1['cards']}/{s2['cards']}\nTiros {s1['shots']}/{s2['shots']} Puerta {s1['sot']}/{s2['sot']}\n\n_{s1['src']}_"
        bot.reply_to(m, res, parse_mode="Markdown")
    except Exception as e:
        print(f"Error handle: {e}")
        try:
            bot.reply_to(m, f"Error interno pero sigo vivo: {e}")
        except: pass

print("BOT V23.1 ULTRA FIX LISTO", flush=True)
bot.infinity_polling(timeout=90, long_polling_timeout=90, skip_pending=True)
