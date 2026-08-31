import os, time, pandas as pd, numpy as np, re, unicodedata, requests
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "OK V24.1 IMG"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

def clean(t):
 t=unicodedata.normalize('NFD',t)
 t=''.join(c for c in t if unicodedata.category(c)!='Mn')
 return t.lower().strip()

def get_stats(team,liga):
 try:
  tc=clean(team)
  df=pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/"+liga+".csv")
  df['hc']=df['HomeTeam'].apply(lambda x: clean(str(x)))
  df['ac']=df['AwayTeam'].apply(lambda x: clean(str(x)))
  m=df['hc'].str.contains(tc,na=False)|df['ac'].str.contains(tc,na=False)
  d=df[m].tail(5)
  if d.empty:
   m2=df['hc'].str.contains(tc[:4],na=False)|df['ac'].str.contains(tc[:4],na=False)
   d=df[m2].tail(5)
  if d.empty: d=df.tail(5)
  ht=int(((d["HTHG"]+d["HTAG"])>0).mean()*100)
  o15=int(((d["FTHG"]+d["FTAG"])>1.5).mean()*100)
  o25=int(((d["FTHG"]+d["FTAG"])>2.5).mean()*100)
  btts=int(((d["FTHG"]>0)&(d["FTAG"]>0)).mean()*100)
  corn=round((d["HC"]+d["AC"]).mean(),1)
  corn_ht=round((d["HC"]+d["AC"]).mean()*0.45,1)
  cards=round((d["HY"]+d["AY"]).mean()+0.3,1)
  return {"name":team.title(),"n":len(d),"liga":liga,"ht":ht,"o15":o15,"o25":o25,"btts":btts,"corn":corn,"corn_ht":corn_ht,"cards":cards}
 except: return None

def detect_liga(t):
 t=clean(t)
 if "braga" in t or "benfica" in t or "porto" in t: return "P1"
 if "brugge" in t or "anderlecht" in t: return "B1"
 if "ajax" in t or "psv" in t: return "N1"
 if "bayern" in t or "dortmund" in t: return "D1"
 if "psg" in t or "marseille" in t: return "F1"
 if "lecce" in t or "inter" in t or "milan" in t or "juve" in t: return "I1"
 if "arsenal" in t or "city" in t or "liverpool" in t or "chelsea" in t: return "E0"
 return "SP1"

def armar(s1,s2):
 avg_ht=int((s1['ht']+s2['ht'])/2)
 avg_o15=int((s1['o15']+s2['o15'])/2)
 avg_o25=int((s1['o25']+s2['o25'])/2)
 avg_btts=int((s1['btts']+s2['btts'])/2)
 rec=""
 if avg_ht>=70: rec+="GOL 1T SI "+str(avg_ht)+"%\n"
 if avg_o15>=80: rec+="OVER 1.5 "+str(avg_o15)+"%\n"
 if avg_o25>=70: rec+="OVER 2.5 "+str(avg_o25)+"%\n"
 if avg_btts>=70: rec+="BTTS SI "+str(avg_btts)+"%\n"
 if not rec: rec="Cerrado\n"
 res=s1['name']+" vs "+s2['name']+" - "+s1['liga']+"\n"
 res+="Gol1T "+str(s1['ht'])+"%/"+str(s2['ht'])+"% -> "+str(avg_ht)+"%\n"
 res+="O1.5 "+str(s1['o15'])+"%/"+str(s2['o15'])+"% O2.5 "+str(s1['o25'])+"%/"+str(s2['o25'])+"%\n"
 res+="BTTS "+str(s1['btts'])+"%/"+str(s2['btts'])+"%\n"
 res+="Corners "+str(s1['corn'])+"/"+str(s2['corn'])+"\n\n"
 res+="RECOM:\n"+rec
 return res

# --- LECTOR DE IMAGENES SIN TESSERACT ---
def leer_imagen_ocr(file_path):
 # usa OCR gratis ocr.space
 try:
  with open(file_path,'rb') as f:
   r=requests.post('https://api.ocr.space/parse/image', files={'file':f}, data={'language':'spa','isOverlayRequired':False}, timeout=20)
  j=r.json()
  if j.get('ParsedResults'):
   return j['ParsedResults'][0]['ParsedText']
  return ""
 except Exception as e:
  print(e); return ""

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
 try:
  bot.reply_to(m,"Leyendo imagen...")
  fid=m.photo[-1].file_id
  info=bot.get_file(fid)
  data=bot.download_file(info.file_path)
  open("temp.jpg","wb").write(data)
  txt=leer_imagen_ocr("temp.jpg")
  if not txt:
   bot.reply_to(m,"No pude leer texto");return
  partidos=re.findall(r'([A-Za-z ]{3,})\s+vs\s+([A-Za-z ]{3,})',txt, re.IGNORECASE)
  if not partidos:
   partidos=re.findall(r'([A-Za-z ]{3,})\s*[-]\s*([A-Za-z ]{3,})',txt)
  if not partidos:
   bot.reply_to(m,"Texto leido:\n"+txt[:400]);return
  for l,v in partidos[:5]:
   l=l.strip(); v=v.strip()
   if len(l)<3 or len(v)<3: continue
   liga=detect_liga(l+" "+v)
   s1=get_stats(l,liga); s2=get_stats(v,liga)
   if s1 and s2:
    bot.send_message(m.chat.id, armar(s1,s2))
 except Exception as e:
  bot.reply_to(m,"Error img: "+str(e))

@bot.message_handler(func=lambda m: True)
def handle(m):
 try:
  txt=clean(m.text)
  if "vs" not in txt: return
  p=re.split(r'\s+v+s+\s*',txt)
  if len(p)<2: p=txt.split("vs")
  l=p[0].strip(); v=p[1].strip()
  liga=detect_liga(l+" "+v)
  s1=get_stats(l,liga); s2=get_stats(v,liga)
  if not s1 or not s2:
   bot.reply_to(m,"No encontre "+l+" o "+v);return
  bot.reply_to(m, armar(s1,s2))
 except Exception as e: print(e)

print("BOT V24.1 IMG LISTO",flush=True)
bot.infinity_polling(timeout=90,long_polling_timeout=90,skip_pending=True)
