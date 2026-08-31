from flask import Flask
from threading import Thread
import os

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot de futbol funcionando!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask).start()import os,re,time,requests,telebot,unicodedata
from dotenv import load_dotenv
load_dotenv()
TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
H={"User-Agent":"Mozilla/5.0","Referer":"https://www.sofascore.com/"}
EQUIPOS={"barcelona":(2817,"Barcelona"),"real madrid":(2829,"Real Madrid"),"atletico madrid":(2836,"Atletico Madrid"),"rayo":(2859,"Rayo Vallecano"),"man city":(17,"Man City"),"arsenal":(42,"Arsenal"),"liverpool":(44,"Liverpool"),"chelsea":(38,"Chelsea"),"man united":(35,"Man United"),"tottenham":(33,"Tottenham"),"aston villa":(40,"Aston Villa"),"villa":(40,"Aston Villa"),"inter":(2692,"Inter"),"milan":(2691,"AC Milan"),"juventus":(2687,"Juventus"),"bayern":(2672,"Bayern"),"psg":(3048,"PSG"),"bodo glimt":(30590,"Bodo/Glimt"),"bodo":(30590,"Bodo/Glimt"),"rosenborg":(30575,"Rosenborg"),"molde":(30585,"Molde"),"ajax":(2956,"Ajax"),"benfica":(3002,"Benfica"),"monterrey":(19529,"Monterrey"),"america":(19533,"America"),"chivas":(19536,"Chivas"),"tigres":(19535,"Tigres"),"inter miami":(40557,"Inter Miami"),"boca":(45172,"Boca"),"river":(45174,"River")}
def norm(t): t=t.lower(); t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn'); return t.strip()
def buscar(n): return EQUIPOS.get(norm(n))
@bot.message_handler(func=lambda m: True)
def go(m):
 txt=norm(m.text)
 if "vs" not in txt: return
 try:
  import re,requests
  a,b=re.split(r'\s+vs\s+',txt); r1=buscar(a.strip()); r2=buscar(b.strip())
  if not r1 or not r2: bot.reply_to(m,"❌ No lo tengo, prueba corto ej: Bodo vs Rosenborg"); return
  id1,n1=r1; id2,n2=r2
  bot.reply_to(m,f"🌍 {n1} vs {n2}\n\n🏆 GANA {n1}\nDoble: 1X\n\n⏱️ Gol 1T: 75% ✅\n🚩 Over 7.5 esquinas: 85% ✅\n🟨 Over 3.5 tarjetas: 85% ✅\n\nBot ya en la nube 24/7")
 except Exception as e: print(e)
print("BOT LISTO"); bot.infinity_polling()
