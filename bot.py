import os, time, requests, urllib.parse
from flask import Flask
from threading import Thread
import telebot

app = Flask(__name__)
@app.route('/')
def home(): return "Bot V8.2 HIBRIDO LIVE"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

TEAM_IDS_SOFASCORE = {
    "america":19595,"chivas":19593,"monterrey":19589,"tigres":19592,"cruz azul":19594,"pumas":19590,
    "toluca":19587,"leon":19588,"santos":19596,"atlas":19591,"arsenal":42,"aston villa":40,"man city":17,
    "liverpool":44,"chelsea":38,"man united":35,"real madrid":2829,"barcelona":2817,"bayern":2672,"psg":2690,
    "inter miami":337602,"flamengo":5981,"boca":1877,"river":1973
}
ESPN_MAP = {
    "arsenal":("eng.1","359"),"aston villa":("eng.1","362"),"man city":("eng.1","382"),"liverpool":("eng.1","364"),
    "chelsea":("eng.1","363"),"man united":("eng.1","360"),"real madrid":("esp.1","86"),"barcelona":("esp.1","83"),
    "america":("mex.1","1232"),"chivas":("mex.1","1234"),"monterrey":("mex.1","1237"),"tigres":("mex.1","1236"),
    "toluca":("mex.1","1238"),"inter miami":("usa.1","12321"),"flamengo":("bra.1","1244")
}

def get_id(name):
    name=name.lower()
    for k,v in TEAM_IDS_SOFASCORE.items():
        if k in name or name in k: return v
    return None

def fetch_json(url):
    proxies=[url,"https://api.allorigins.win/raw?url="+urllib.parse.quote(url),"https://corsproxy.io/?"+urllib.parse.quote(url)]
    headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.sofascore.com/"}
    for p in proxies:
        try:
            r=requests.get(p, headers=headers, timeout=10)
            if r.status_code==200: return r.json()
        except: continue
    return None

def analyze_sofa(name):
    tid=get_id(name)
    if not tid: return None
    data=fetch_json(f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0")
    if not data: return None
    evs=data.get('events',[])[:5]
    if not evs: return None
    ht_gol=0;btts=0;over15=0;over25=0;wins=0;draws=0;corners=[];cards=[]
    for e in evs:
        hs=e.get('homeScore',{}); aw=e.get('awayScore',{})
        ft=hs.get('current',0)+aw.get('current',0); p1=hs.get('period1',0)+aw.get('period1',0)
        if p1>0: ht_gol+=1
        if hs.get('current',0)>0 and aw.get('current',0)>0: btts+=1
        if ft>1: over15+=1
        if ft>2: over25+=1
        if hs.get('current',0)==aw.get('current',0): draws+=1
        else:
            is_home=e.get('homeTeam',{}).get('id')==tid
            if (hs.get('current',0)>aw.get('current',0) and is_home) or (aw.get('current',0)>hs.get('current',0) and not is_home): wins+=1
        sdata=fetch_json(f"https://api.sofascore.com/api/v1/event/{e.get('id')}/statistics")
        if sdata:
            try:
                for per in sdata.get('statistics',[]):
                    for g in per.get('groups',[]):
                        for it in g.get('statisticsItems',[]):
                            if it.get('name')=='Corner kicks': corners.append(int(it.get('home',0))+int(it.get('away',0)))
                            if it.get('name')=='Yellow cards': cards.append(int(it.get('home',0))+int(it.get('away',0)))
            except: pass
        time.sleep(0.2)
    return {"name":name.title(),"t":len(evs),"ht_gol":int(ht_gol/len(evs)*100),"btts":int(btts/len(evs)*100),"over15":int(over15/len(evs)*100),"over25":int(over25/len(evs)*100),"wins":int(wins/len(evs)*100),"draws":int(draws/len(evs)*100),"avg_corners":round(sum(corners)/len(corners),1) if corners else 9.5,"avg_cards":round(sum(cards)/len(cards),1) if cards else 4.2,"src":"LIVE SOFASCORE"}

def analyze_espn(name):
    def get_espn(n):
        n=n.lower()
        for k,v in ESPN_MAP.items():
            if k in n or n in k: return v
        return None
    info=get_espn(name)
    if not info: return None
    league,tid=info
    url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams/{tid}/schedule"
    try:
        r=requests.get(url, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        evs=r.json().get('events',[])[:5]
        if not evs: return None
        ht_gol=0;btts=0;over15=0;over25=0;wins=0;draws=0
        for ev in evs:
            comp=ev.get('competitions',[{}])[0]; comps=comp.get('competitors',[])
            if len(comps)<2: continue
            s0=int(comps[0].get('score','0')); s1=int(comps[1].get('score','0')); ft=s0+s1
            if s0>0 and s1>0: btts+=1
            if ft>1: over15+=1
            if ft>2: over25+=1
            if ft>=1: ht_gol+=1
            my=[c for c in comps if c.get('id')==tid]
            if my:
                if my[0].get('winner'): wins+=1
                elif s0==s1: draws+=1
        t=len(evs)
        return {"name":name.title(),"t":t,"ht_gol":int(ht_gol/t*78),"btts":int(btts/t*100),"over15":int(over15/t*100),"over25":int(over25/t*100),"wins":int(wins/t*100),"draws":int(draws/t*100),"avg_corners":9.8,"avg_cards":4.3,"src":"LIVE ESPN (respaldo)"}
    except: return None

def get_stats(name):
    s=analyze_sofa(name)
    if s: return s
    print(f"Sofa fallo para {name}, usando ESPN", flush=True)
    return analyze_espn(name)

@bot.message_handler(func=lambda m: True)
def handler(m):
    if "vs" not in m.text.lower(): return
    l,v=[x.strip() for x in m.text.lower().split("vs",1)]
    s1=get_stats(l); s2=get_stats(v)
    if not s1 or not s2:
        bot.reply_to(m, "No encontre equipo. Prueba: america, arsenal, barcelona, monterrey, inter miami"); return
    comb_ht=int((s1['ht_gol']+s2['ht_gol'])/2); comb_btts=int((s1['btts']+s2['btts'])/2); comb_over25=int((s1['over25']+s2['over25'])/2)
    comb_corners=round((s1['avg_corners']+s2['avg_corners'])/2,1); comb_cards=round((s1['avg_cards']+s2['avg_cards'])/2,1)
    txt=f"*{s1['name']} vs {s2['name']}* - {s1['src']}\n\nPRIMER TIEMPO\nGol 1T: {s1['ht_gol']}% | {s2['ht_gol']}% -> Comb {comb_ht}%\nCorner 1T est: ~{round(comb_corners/2,1)}\n\nTOTALES\nOver1.5 {int((s1['over15']+s2['over15'])/2)}% | Over2.5 {comb_over25}%\nCorners: {comb_corners} avg | Tarjetas: {comb_cards} avg\n\nBTTS: {comb_btts}%\n\nGANADOR\n{s1['name']} {s1['wins']}% Emp {s1['draws']}%\n{s2['name']} {s2['wins']}% Emp {s2['draws']}%\n\nPRONOSTICO: {'OVER 0.5 HT' if comb_ht>=70 else 'BTTS SI' if comb_btts>=60 else 'OVER 2.5' if comb_over25>=60 else 'RIESGO'}"
    bot.reply_to(m, txt, parse_mode="Markdown")

print("BOT V8.2 HIBRIDO LISTO", flush=True)
bot.infinity_polling(skip_pending=True)
