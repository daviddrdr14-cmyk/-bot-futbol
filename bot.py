import os, time, pandas as pd, numpy as np, re, unicodedata
from flask import Flask
from threading import Thread
import telebot
from PIL import Image
import pytesseract

app = Flask(__name__)
@app.route('/')
def home(): return "OK V24"
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
  tiros=[];sot=[]
  for _,r in d.iterrows():
   if tc in r['hc']:
    tiros.append(r.get("HS",12));sot.append(r.get("HST",4))
   else:
    tiros.append(r.get("AS",11));sot.append(r.get("AST",3.5))
  ht=int(((d["HTHG"]+d["HTAG"])>0).mean()*100)
  o15=int(((d["FTHG"]+d["FTAG"])>1.5).mean()*100)
  o25=int(((d["FTHG"]+d["FTAG"])>2.5).mean()*100)
  btts=int(((d["FTHG"]>0)&(d["FTAG"]>0)).mean()*100)
  corn=round((d["HC"]+d["AC"]).mean(),1)
  corn_ht=round((d["HC"]+d["AC"]).mean()*0.45,1)
  cards=round((d["HY"]+d["AY"]).mean()+0.3,1)
  shots=round(float(np.mean(tiros)),1)
  soton=round(float(np.mean(sot)),1)
  return {"name":team.title(),"n":len(d),"liga":liga,"ht":ht,"o15":o15,"o25":o25,"btts":btts,"corn":corn,"corn_ht":corn_ht,"cards":cards,"shots":shots,"sot":soton}
 except: return None

def detect_liga(t):
 t=clean(t)
 if "benfica" in t or "porto" in t or "braga" in t: return "P1"
 if "estoril" in t or "guimaraes" in t: return "P1"
 if "brugge" in t or "anderlecht" in t: return "B1"
 if "ajax" in t or "psv" in t: return "N1"
 if "bayern" in t or "dortmund" in t: return "D1"
 if "psg" in t or "marseille" in t: return "F1"
 if "lecce" in t or "atalanta" in t or "inter" in t: return "I1"
 if "milan" in t or "juventus" in t or "juve" in t: return "I1"
 if "napoli" in t or "roma" in t: return "I1"
 if "arsenal" in t or "city" in t: return "E0"
 if "liverpool" in t or "chelsea" in t or "united" in t: return "E0"
 return "SP1"

def armar_respuesta(s1,s2):
 avg_ht=int((s1['ht']+s2['ht'])/2)
 avg_o15=int((s1['o15']+s2['o15'])/2)
 avg_o25=int((s1['o25']+s2['o25'])/2)
 avg_btts=int((s1['btts']+s2['btts'])/2)
 avg_corn=(s1['corn']+s2['corn'])/2
 rec=""
 if avg_ht>=70: rec+="GOL 1T SI "+str(avg_ht)+"%\n"
 if avg_o15>=80: rec+="OVER 1.5 "+str(avg_o15)+"%\n"
 if avg_o25>=70: rec+="OVER 2.5 "+str(avg_o25)+"%\n"
 if avg_btts>=70: rec+="BTTS SI "+str(avg_btts)+"%\n"
 if avg_corn>=9: rec+="OVER 8.5 CORNERS "+str(round(avg_corn,1))+"\n"
 if not rec: rec="Partido cerrado sin valor claro\n"
 res=s1['name']+" vs "+s2['name']+" - "+s1['liga']+" Ult "+str(s1['n'])+"J\n"
 res+="1T REAL\n"
 res+="Gol 1T: "+str(s1['ht'])+"% | "+str(s2['ht'])+"% -> "+str(avg_ht)+"%\n"
 res+="Corner 1T: "+str(s1['corn_ht'])+" | "+str(s2['corn_ht'])+"\n\n"
 res+="TOTALES\n"
 res+="O1.5 "+str(s1['o15'])+"%/"+str(s2['o15'])+"% O2.5 "+str(s1['o25'])+"%/"+str(s2['o25'])+"%\n"
 res+="BTTS "+str(s1['btts'])+"%/"+str(s2['btts'])+"%\n"
 res+="Corners "+str(s1['corn'])+"/"+str(s2['corn'])+" Tarj "+str(s1['cards'])+"/"+str(s2['cards'])+"\n"
 res+="Tiros "+str(s1['shots'])+"/"+str(s2['shots'])+" Puerta "+str(s1['sot'])+"/"+str(s2['sot'])+"\n\n"
 res+="RECOM:\n"+rec
 return res

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
 try:
  bot.reply_to(m,"Leyendo imagen...")
  fid=m.photo[-1].file_id
  info=bot.get_file(fid)
  data=bot.download_file(info.file_path)
  open("temp.jpg","wb").write(data)
  img=Image.open("temp.jpg")
  txt=pytesseract.image_to_string(img)
  # busca vs
  partidos=re.findall(r'([A-Za-z0-9 ]{3,})\s+vs\s+([A-Za-z0-9 ]{3,})',txt, re.IGNORECASE)
  if not partidos:
   partidos=re.findall(r'([A-Za-z0-9 ]{3,})\s+-\s+([A-Za-z0-9 ]{3,})',txt)
  if not partidos:
   bot.reply_to(m,"No vi un vs en la imagen. Texto que lei:\n"+txt[:400])
   return
  for l,v in partidos[:5]:
   l=l.strip(); v=v.strip()
   if len(l)<3 or len(v)<3: continue
   liga=detect_liga(l+" "+v)
   s1=get_stats(l,liga); s2=get_stats(v,liga)
   if s1 and s2:
    res=armar_respuesta(s1,s2)
    bot.send_message(m.chat.id,res)
   else:
    bot.send_message(m.chat.id,"No encontre "+l+" o "+v)
 except Exception as e:
  print(e)
  bot.reply_to(m,"Error imagen: "+str(e))

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
  res=armar_respuesta(s1,s2)+"\nfootball-data "+liga+" REAL"
  bot.reply_to(m,res)
 except Exception as e: print(e)

print("BOT V24 CON IMAGENES LISTO",flush=True)
bot.infinity_polling(timeout=90,long_polling_timeout=90,skip_pending=True)
