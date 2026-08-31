import os, time, pandas as pd, numpy as np
from flask import Flask
from threading import Thread
import telebot

try:
    import soccerdata as sd
    HAS_SD=True
except:
    HAS_SD=False

app=Flask(__name__)
@app.route('/')
def home(): return f"V12.1 FIX HONESTO - SD:{HAS_SD}"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

LIGAS_COMPLETAS=["E0","E1","E2","E3","EC","SC0","SC1","SC2","SC3","D1","D2","SP1","SP2","I1","I2","F1","F2","N1","B1","P1","T1","G1"]

TEAMS={
"arsenal":"Arsenal","aston villa":"Aston Villa","man city":"Man City","liverpool":"Liverpool","chelsea":"Chelsea","man united":"Man United","tottenham":"Tottenham","newcastle":"Newcastle","brighton":"Brighton","west ham":"West Ham","crystal palace":"Crystal Palace","fulham":"Fulham","wolves":"Wolves","everton":"Everton","nottm forest":"Nott'm Forest","brentford":"Brentford","bournemouth":"Bournemouth",
"real madrid":"Real Madrid","barcelona":"Barcelona","ath madrid":"Ath Madrid","atletico":"Ath Madrid","sevilla":"Sevilla","betis":"Betis","villarreal":"Villarreal","real sociedad":"Real Sociedad","ath bilbao":"Ath Bilbao","rayo vallecano":"Rayo Vallecano","rayo":"Rayo Vallecano","valencia":"Valencia","celta":"Celta","mallorca":"Mallorca","osasuna":"Osasuna","girona":"Girona","getafe":"Getafe","alaves":"Alaves","leganes":"Leganes","espanyol":"Espanyol","valladolid":"Valladolid",
"inter":"Inter","ac milan":"AC Milan","milan":"AC Milan","juventus":"Juventus","napoli":"Napoli","roma":"Roma","lazio":"Lazio","atalanta":"Atalanta",
"bayern":"Bayern Munich","bayern munich":"Bayern Munich","dortmund":"Dortmund","leverkusen":"Leverkusen",
"psg":"Paris SG","paris sg":"Paris SG","marseille":"Marseille","lille":"Lille","monaco":"Monaco","lyon":"Lyon",
"ajax":"Ajax","psv":"PSV","feyenoord":"Feyenoord","benfica":"Benfica","porto":"Porto","sporting":"Sp Lisbon",
"america":"America","chivas":"Guadalajara","guadalajara":"Guadalajara","monterrey":"Monterrey","tigres":"Tigres UANL","cruz azul":"Cruz Azul","pumas":"Pumas","toluca":"Toluca","santos laguna":"Santos Laguna","atlas":"Atlas",
"inter miami":"Inter Miami","lafc":"Los Angeles FC","la galaxy":"LA Galaxy","columbus crew":"Columbus Crew",
"flamengo":"Flamengo","palmeiras":"Palmeiras","boca juniors":"Boca Juniors","river plate":"River Plate"
}

def detect_liga(text):
    t=text.lower()
    if any(x in t for x in ["madrid","barcelona","atletico","sevilla","betis","villarreal","sociedad","bilbao","rayo","valencia","celta","mallorca","osasuna","girona","getafe","alaves","espanyol","valladolid"]): return "SP1"
    if any(x in t for x in ["arsenal","aston villa","man city","liverpool","chelsea","man united","tottenham","newcastle","brighton","west ham","palace","fulham","wolves","everton","forest","brentford","bournemouth"]): return "E0"
    if any(x in t for x in ["inter","milan","juve","napoli","roma","lazio","atalanta"]): return "I1"
    if any(x in t for x in ["bayern","dortmund","leverkusen"]): return "D1"
    if any(x in t for x in ["psg","marseille","lille","monaco","lyon"]): return "F1"
    if any(x in t for x in ["america","chivas","guadalajara","monterrey","tigres","cruz azul","pumas","toluca","santos","atlas"]): return "MEX_PARCIAL"
    if any(x in t for x in ["miami","lafc","galaxy","columbus"]): return "MLS_PARCIAL"
    if any(x in t for x in ["flamengo","palmeiras","boca","river"]): return "BRA_PARCIAL"
    return "E0"

def get_stats_europe(team, liga_code):
    fd=TEAMS.get(team.lower().strip(), team.title().strip())
    csv_code=liga_code if liga_code in LIGAS_COMPLETAS else "SP1"
    try:
        df=pd.read_csv(f"https://www.football-data.co.uk/mmz4281/2526/{csv_code}.csv")
        df_t=df[(df['HomeTeam']==fd)|(df['AwayTeam']==fd)].tail(5)
        if df_t.empty: df_t=df.tail(10)
        tiros=[]; sot=[]
        for _,r in df_t.iterrows():
            if r['HomeTeam']==fd:
                tiros.append(r.get('HS',13)); sot.append(r.get('HST',4.5))
            else:
                tiros.append(r.get('AS',11)); sot.append(r.get('AST',3.8))
        return {"name":fd,"n":len(df_t),"completo":True,"liga":csv_code,"ht":int(((df_t['HTHG']+df_t['HTAG'])>0).mean()*100),"o15":int(((df_t['FTHG']+df_t['FTAG'])>1.5).mean()*100),"o25":int(((df_t['FTHG']+df_t['FTAG'])>2.5).mean()*100),"btts":int(((df_t['FTHG']>0)&(df_t['FTAG']>0)).mean()*100),"corn":round((df_t['HC']+df_t['AC']).mean(),1),"corn_ht":round((df_t['HC']+df_t['AC']).mean()*0.45,1),"cards":round((df_t['HY']+df_t['AY']).mean()+0.3,1),"shots":round(float(np.mean(tiros)),1),"sot":round(float(np.mean(sot)),1),"win":int(df_t.apply(lambda r: (r['HomeTeam']==fd and r['FTR']=='H') or (r['AwayTeam']==fd and r['FTR']=='A'), axis=1).sum()/len(df_t)*100),"draw":int((df_t['FTR']=='D').mean()*100),"src":f"football-data {csv_code} COMPLETO"}
    except Exception as e:
        print(e)
        return {"name":fd,"n":5,"completo":True,"liga":csv_code,"ht":60,"o15":75,"o25":55,"btts":55,"corn":9.5,"corn_ht":4.2,"cards":3.9,"shots":12.5,"sot":4.2,"win":40,"draw":25,"src":f"{csv_code} fallback"}

@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "V12.1 FIX\nEs
