import os, time, requests, urllib.parse
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V7 FULL STATS LIVE"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

TEAM_IDS = {
    "america":19595,"chivas":19593,"guadalajara":19593,"monterrey":19589,"rayados":19589,"tigres":19592,
    "cruz azul":19594,"pumas":19590,"toluca":19587,"leon":19588,"santos":19596,"atlas":19591,"pachuca":19597,
    "necaxa":19598,"tijuana":122122,"juarez":122123,"puebla":19599,"queretaro":19600,"mazatlan":122121,"san luis":122124,
    "arsenal":42,"man city":17,"liverpool":44,"chelsea":38,"man united":35,"aston villa":40,"newcastle":39,"tottenham":33,"brighton":50,
    "real madrid":2829,"barcelona":2817,"atletico":2836,"sevilla":2834,"betis":2815,"villarreal":2824,
    "inter":2697,"milan":2692,"juventus":2687,"napoli":2702,"roma":2709,"bayern":2672,"dortmund":2673,"leverkusen":2681,"psg":2690,
    "inter miami":337602,"flamengo":5981,"palmeiras":4750,"river":1973,"boca":1877
}

def get_id(n):
    n=n.lower()
    for k,v in TEAM_IDS.items():
        if k in n or n in k: return v
    return None

def fetch_json(url):
    proxies = [url, f"https://api.allorigins.win/raw?url={urllib.parse.quote(url)}", f"https://corsproxy.io/?{urllib.parse.quote(url)}"]
    headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.sofascore.com/"}
    for p in proxies:
        try:
            r=requests.get(p, headers=headers, timeout=12)
            if r.status_code==200: return r.json()
        except: continue
    return None

def analyze_team(name):
    tid=get_id(name)
    if not tid: return None
    data=fetch_json(f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0")
    if not data: return None
    evs=data.get('events',[])[:5]
    if not evs: return None
    
    ht_gol=0; btts=0; over15=0; over25=0; wins=0; draws=0; loses=0; total_corners=[]; total_cards=[]; ht_corners=[]
    
    for e in evs:
        hs=e.get('homeScore',{}); aw=e.get('awayScore',{})
        ft = hs.get('current',0)+aw.get('current',0)
        p1 = hs.get('period1',0)+aw.get('period1',0)
        if p1>0: ht_gol+=1
        if hs.get('current',0)>0 and aw.get('current',0)>0: btts+=1
        if ft>1.5: over15+=1
        if ft>2.5: over25+=1
        
        # quien gana
        is_home = e.get('homeTeam',{}).get('id')==tid
        if hs.get('current',0)>aw.get('current',0): wins+=1 if is_home else loses+=1
        elif hs.get('current',0)<aw.get('current',0): loses+=1 if is_home else wins+=1
        else: draws+=1

        # corners y tarjetas - pide detalle del partido
        ev_id=e.get('id')
        sdata=fetch_json(f"https://api.sofascore.com/api/v1/event/{ev_id}/statistics")
        if sdata:
            try:
                all_stats=sdata.get('statistics',[])
                for period in all_stats:
                    groups=period.get('groups',[])
                    for g in groups:
                        for it in g.get('statisticsItems',[]):
                            if it.get('name')=='Corner kicks': total_corners.append(int(it.get('home',0))+int(it.get('away',0)))
                            if it.get('name')=='Yellow cards': total_cards.append(int(it.get('home',0))+int(it.get('away',0)))
                            if it.get('name')=='Yellow cards': pass
            except: pass
        time.sleep(0.3)

    return {
        "name": name.title(),
        "t": len(evs),
        "ht_gol": int(ht_gol/len(evs)*100),
        "btts": int(btts/len(evs)*100),
        "over15": int(over15/len(evs)*100),
        "over25": int(over25/len(evs)*100),
        "wins": int(wins/len(evs)*100),
        "draws": int(draws/len(evs)*100),
        "avg_corners": round(sum(total_corners)/len(total_corners),1) if total_corners else 9.2,
        "avg_cards": round(sum(total_cards)/len(total_cards),1) if total_cards else 4.5,
        "src": "LIVE SOFASCORE ✅"
    }

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Formato: `Equipo vs Equipo`\nEj: America vs Chivas\n\nTe doy: Gol 1T, Corners 1T*, Goles Tot, Corners Tot, Tarjetas Tot, BTTS y 1X2\n*Corner 1T estimado de total", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    s1=analyze_team(l); s2=analyze_team(v)
    if not s1 or not s2:
        bot.reply_to(m, "No pude sacar LIVE, SofaScore bloqueó. Intenta en 20 seg.")
        return
    comb_ht=int((s1['ht_gol']+s2['ht_gol'])/2)
    comb_btts=int((s1['btts']+s2['btts'])/2)
    comb_over25=int((s1['over25']+s2['over25'])/2)
    comb_corners=round((s1['avg_corners']+s2['avg_corners'])/2,1)
    comb_cards=round((s1['avg_cards']+s2['avg_cards'])/2,1)

    txt=f"""📊 *{s1['name']} vs {s2['name']}* 
_{s1['src']}_ - Ult 5 partidos LIVE

*PRIMER TIEMPO*
Gol 1T: {s1['name']} {s1['ht_gol']}% | {s2['name']} {s2['ht_gol']}% -> *Comb {comb_ht}%*
Corner 1T (est): ~{round(comb_corners/2,1)} (de {comb_corners} tot)

*TOTALES*
Goles Tot: Over 1.5 {int((s1['over15']+s2['over15'])/2)}% | Over 2.5 {comb_over25}%
Corners Tot: {comb_corners} avg ({s1['avg_corners']} + {s2['avg_corners']})
Tarjetas Tot: {comb_cards} avg

*AMBOS ANOTAN*
BTTS: {s1['btts']}% / {s2['btts']}% -> *Comb {comb_btts}%*

*GANADOR*
{s1['name']}: Gana {s1['wins']}% Emp {s1['draws']}%
{s2['name']}: Gana {s2['wins']}% Emp {s2['draws']}%

🔥 *PRONÓSTICO: {'OVER 0.5 HT ✅' if comb_ht>=70 else 'BTTS SI' if comb_btts>=60 else 'OVER 2.5' if comb_over25>=60 else 'RIESGO'}*
"""
    bot.reply_to(m, txt, parse_mode="Markdown")

print("BOT V7 FULL LIVE LISTO", flush=True)
bot.infinity_polling(skip_pending=True)
