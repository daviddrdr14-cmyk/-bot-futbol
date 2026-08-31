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
def home(): return f"V12 HONESTA 22 Ligas + Americas PARCIAL - SD:{HAS_SD}"
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# 22 LIGAS REALES QUE SI EXISTEN EN football-data.co.uk/mmz4281/2526/
LIGAS_COMPLETAS = ["E0","E1","E2","E3","EC","SC0","SC1","SC2","SC3","D1","D2","SP1","SP2","I1","I2","F1","F2","N1","B1","P1","T1","G1"]

TEAMS={
 # E0 Premier
 "arsenal":"Arsenal","aston villa":"Aston Villa","man city":"Man City","liverpool":"Liverpool","chelsea":"Chelsea","man united":"Man United","tottenham":"Tottenham","newcastle":"Newcastle","brighton":"Brighton","west ham":"West Ham","crystal palace":"Crystal Palace","fulham":"Fulham","wolves":"Wolves","everton":"Everton","nottm forest":"Nott'm Forest","brentford":"Brentford","bournemouth":"Bournemouth",
 # SP1 LaLiga - COMPLETA
 "real madrid":"Real Madrid","barcelona":"Barcelona","atletico madrid":"Ath Madrid","atletico":"Ath Madrid","sevilla":"Sevilla","betis":"Betis","villarreal":"Villarreal","real sociedad":"Real Sociedad","sociedad":"Real Sociedad","athletic bilbao":"Ath Bilbao","athletic":"Ath Bilbao","bilbao":"Ath Bilbao","rayo vallecano":"Rayo Vallecano","rayo":"Rayo Vallecano","valencia":"Valencia","celta":"Celta","mallorca":"Mallorca","osasuna":"Osasuna","girona":"Girona","getafe":"Getafe","alaves":"Alaves","leganes":"Leganes","espanyol":"Espanyol","valladolid":"Valladolid","las palmas":"Las Palmas",
 # SP2
 "levante":"Levante","elche":"Elche",
 # I1 Serie A
 "inter":"Inter","milan":"AC Milan","juventus":"Juventus","napoli":"Napoli","roma":"Roma","lazio":"Lazio","atalanta":"Atalanta","fiorentina":"Fiorentina",
 # D1 Bundesliga
 "bayern munich":"Bayern Munich","bayern":"Bayern Munich","dortmund":"Dortmund","leverkusen":"Leverkusen","leipzig":"RB Leipzig",
 # F1 Ligue1
 "psg":"Paris SG","paris sg":"Paris SG","marseille":"Marseille","lyon":"Lyon","lille":"Lille","monaco":"Monaco",
 # N1 Eredivisie
 "ajax":"Ajax","psv":"PSV","feyenoord":"Feyenoord",
 # P1 Portugal
 "benfica":"Benfica","porto":"Porto","sporting":"Sp Lisbon",
 # AMERICAS - FBRef PARCIAL
 "america":"America","chivas":"Guadalajara","guadalajara":"Guadalajara","monterrey":"Monterrey","tigres":"Tigres UANL","cruz azul":"Cruz Azul","pumas":"Pumas","toluca":"Toluca","santos laguna":"Santos Laguna","atlas":"Atlas","leon":"Leon",
 "inter miami":"Inter Miami","lafc":"Los Angeles FC","la galaxy":"LA Galaxy","columbus crew":"Col
