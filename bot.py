import os, time, pandas as pd, re
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "OK V26 TEXTO"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(2)

def clean(t):
 t=t.lower()
 t=t.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
 return t.strip()

def get_stats(team,liga):
 try:
  tc=clean(team)
  df=pd.read_csv(f"https://www.football-data.co.uk/mmz4281/2526/{liga}.csv")
  df['hc']=df['HomeTeam'].apply(lambda x: clean(str(x)))
  df['ac']=df['AwayTeam'].apply(lambda x: clean(str(x)))
  m=df['hc'].str.contains(tc,na=False)|df['ac'].str.contains(tc,na=False)
  d=df[m].tail(5)
  if d.empty:
   d=df[df['hc'].str.contains(tc[:4],na=False)|df['ac'].str.contains(tc[:4],na=False)].tail(5)
  if d.empty: d=df.tail(5)
  ht=int(((d["HTHG"]+d["HTAG"])>0).mean()*100)
  o15=int(((d["FTHG"]+d["FTAG"])>1.5).mean()*100)
  o25=int(((d["FTHG"]+d["FTAG"])>2.5).mean()*100)
  btts=int(((d["FTHG"]>0)&(d["FTAG"]>0)).mean()*100)
  corn=round((d["HC"]+d["AC"]).mean(),1)
  corn_ht=round(corn*0.45,1)
  return {"name":team.title(),"ht":ht,"o15":o15,"o25":o25,"btts":btts,"corn":corn,"corn_ht":corn_ht}
 except: return None

def detect_liga(t):
 t=clean(t)
 if "osasuna" in t or "getafe" in t or "villarreal" in t: return "SP1"
 if "lecce" in t or "roma" in t: return "I1"
 if "braga" in t or "benfica" in t: return "P1"
 return "SP1"

def armar(s1,s2):
 avg_ht=int((s1['ht']+s2['ht'])/2)
 avg_o15=int((s1['o15']+s2['o15'])/2)
 avg_o25=int((s1['o25']+s2['o25'])/2)
 avg_btts=int((s1['btts']+s2['btts'])/2)
 rec=""
 if avg_ht>=60: rec+=f"GOL 1T SI {avg_ht}%\n"
 else: rec+=f"GOL 1T NO {100-avg_ht}%\n"
 if avg_o15>=70: rec+=f"OVER 1.5 {avg_o15}%\n"
 if avg_o25>=60: rec+=f"OVER 2.5 {avg_o25}%\n"
 if avg_btts>=60: rec+=f"BTTS SI {avg_btts}%\n"
 else: rec+=f"BTTS NO {100-avg_btts}%\n"
 rec+=f"CORNERS { (s1['corn']+s2['corn'])/2:.1f} / 1T { (s1['corn_ht']+s2['corn_ht'])/2:.1f}\n"

 return f"{s1['name']} vs {s2['name']}\nHT {s1['ht']}%/{s2['ht']}% -> {avg_ht}%\nO1.5 {s1['o15']}%/{s2['o15']}% O2.5 {s1['o25']}%/{s2['o25']}%\nBTTS {s1['btts']}%/{s2['btts']}%\n\nRECOM:\n{rec}"

# IGNORA FOTOS - NO MAS "NO PUDE LEER TEXTO"
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
 bot.reply_to(m,"Mándamelo escrito porfa: Ej. Osasuna vs Getafe")

@bot.message_handler(func=lambda m: True)
def handle(m):
 try:
  txt=m.text
  if not txt or "vs" not in txt.lower(): return
  p=re.split(r'\s+vs\s+',txt, flags=re.IGNORECASE)
  if len(p)<2: return
  l=p[0].strip(); v=p[1].strip()
  if len(l)<3 or len(v)<3: return
  liga=detect_liga(l+" "+v)
  s1=get_stats(l,liga); s2=get_stats(v,liga)
  if not s1 or not s2:
   bot.reply_to(m,f"No encontre {l} o {v} en {liga}"); return
  bot.reply_to(m, armar(s1,s2))
 except Exception as e:
  print(e)

print("BOT V26 TEXTO LISTO",flush=True)
bot.infinity_polling(timeout=90,long_polling_timeout=90,skip_pending=True)
