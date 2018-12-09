from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import requests
from bs4 import BeautifulSoup
import os
import math
import re
import random


def CreateHTbase(S):
    S = S.lower()
    HT = {}
    for i,E in enumerate(S[:len(S)-1]):
        if (E+S[i+1]) not in HT.keys():
            HT.update({E+S[i+1]: 0})
    return HT

def CompareHT (HT0, HT1):
    res = 0
    nonZero = 0
    for K in (HT0.keys()):
        if (HT0[K] + HT1[K])!= 0:
            res = res +  math.fabs(HT0[K] - HT1[K])/(HT0[K] + HT1[K])
            nonZero = nonZero + 1
    if nonZero > 0:
        res = res/nonZero
        return res
    return -1

def CreateHT(S, HTbase):
    S = S.lower()
    HT = HTbase.copy()
    for i,E in enumerate(S[:len(S)-1]):
        if (E+S[i+1]) in HT.keys():
            HT[E+S[i+1]] = HT[E+S[i+1]] + 1
    for K in HT.keys():
        HT[K] = HT[K]/len(S)
    return HT

def PrepareString(S):
    stoplist = '\r\n\t!@#$%^&*()-=_+{}[]:;,.\'"<>/?|\\ '
    for char in stoplist:
        S = S.replace(char, "")
    return S

def PrepareString2(S):
    words = re.findall(r"[\w']+", S.lower())
    S = ''
    for w in words:
        S = S + w + ' '
    return S

def FindPlagiatOne(S):
    #print(S)
    #print('==============================')

    Comment = {}
    Similarity = 1
    #HT0 = CreateHT(PrepareString(S))

    url0 ='http://www.google.com/search?q='
    #h = {'User-Agent': HTTPheaders[0]}
    #h = {'User-Agent': HTTPheaders[random.randint(0,len(HTTPheaders)-1)]}
    #print(h['User-Agent'])
    #page = requests.get(url0 + S, headers=h)
    page = requests.get(url0 + S)
    if page.status_code != 200:
        print('Blocked by Google!')
        return -1, {}
    soup0 = BeautifulSoup(page.text, "html.parser")
    h3 = soup0.find_all('div',class_="g")

    #S = PrepareString(S)
    HTbase = CreateHTbase(S)
    HT0 = CreateHT(S, HTbase)


    for elem in h3:
        Bad = False
        tmp = elem.find("h3")
        if tmp != None:
            PlagTitle = elem.find("h3").text
        else:
            Bad = True
        if not Bad:
            tmp = elem.find("div", {"class": "s"})
            if tmp == None:
                Bad = True
            else:
                if (tmp.find('cite')==None):
                    PlagText = tmp.text
                else:
                    PlagText = tmp.find('span',{'class':'st'}).text
        if not Bad:
            tmp = elem.find({'cite':'class'})
            if tmp != None:
                PlagLink = elem.find({'cite':'class'}).text
            else:
                Bad = True
        if not Bad:
            #print(PlagTitle)
            #print(PlagLink)
            #print(PlagText)
            localComment = None
            localSimilarity = 1
            PlagText2 = PrepareString2(PlagText)
            #HT1 = CreateHT(PrepareString(PlagText))
            if (len(S)<=len(PlagText2)):
                #for k in range(0, len(PlagText) - len(S), int(len(S) / 8 - 1)):
                for k in range(0,len(PlagText2)-len(S),3):
                    S0 = PlagText2[k:k+len(S)]
                    HT1 = CreateHT(S0,HTbase)
                    SD = CompareHT(HT1, HT0)
                    if (SD < Similarity):
                        Similarity = SD
                    if (SD < 0.5):
                        if (SD < localSimilarity):
                            localSimilarity = SD
                            localComment = [round(SD*100, 3), PlagLink, PlagText]
                if localComment != None:
                    Comment[PlagTitle] = localComment
            else:
                HT1 = CreateHT(PlagText2,HTbase)
                SD = CompareHT(HT1, HT0)
                if (SD < Similarity):
                    Similarity = SD
                if (SD < 0.5):
                    Comment[PlagTitle] = [round(SD * 100, 3), PlagLink, PlagText]


            #print ('Уникальность: {0} %'.format(Similarity*100))
            #print()
    return Similarity, Comment

def FindPlagiatGeneral(S, TopCount):
    Comments = {}
    MainSimilarity = 0
    MaxRequestLength = 25
    WindowLength = 13
    #words = S.split('.', ' ', ',', '!', '?', ':', ';', '(', ')', '[', ']')
    words = re.findall(r"[\w']+", S.lower())
    start = 0
    if len(words) <= MaxRequestLength:
        partS = ''
        for W in words:
            partS = partS + W + ' '
        #print(partS)
        Res = FindPlagiatOne(partS)
        if (Res[0] == -1):
            return -1, {}
        MainSimilarity = round((Res[0])*100, 3)
        if Res[1] != None:
            Comments = Res[1].copy()
    else:
        partcount = 0
        while (start + MaxRequestLength) <= len(words):
            partS = ''
            for W in words[start:start+MaxRequestLength]:
                partS = partS + W + ' '
            start = start + WindowLength
            partcount = partcount + 1
            #print (partS)
            #print(start)
            Res = FindPlagiatOne(partS)
            if (Res[0] == -1):
                return -1, {}
            if Res[0]>0:
                MainSimilarity = MainSimilarity + 1/ Res[0]
            else:
                MainSimilarity = MainSimilarity + 1/0.000000001
            for K in Res[1].keys():
                if K in Comments.keys():
                    if (Res[1][K][0] < Comments[K][0]):
                        Comments[K] = Res[1][K]
                Comments[K] = Res[1][K]
            time.sleep(random.randint(8,13))
        if MainSimilarity > 0:
            MainSimilarity = round((partcount/MainSimilarity)*100, 3)
    #print('ok')
    CommentsSorted = {}

    if len(Comments.keys()) < TopCount:
        TopCount = len(Comments.keys())
    while len(CommentsSorted.keys()) < TopCount:
        minSim = 1000
        minK = None
        for K in Comments.keys():
            if (K not in CommentsSorted.keys()):
                if (Comments[K][0] < minSim):
                    minSim = Comments[K][0]
                    minK = K
        CommentsSorted[minK] = Comments[minK]

    return MainSimilarity, CommentsSorted

def FindPlagiatTelegramm(S, TopCount):
    outText = ''
    res = FindPlagiatGeneral(S, TopCount)
    if res[0] == -1:
        outText = 'Извините, сервис временно не работает! Бдительный поисковик ограничил доступ...'
    else:
        outText = 'ПАМЯТКА: 0%-25% плагиат, 0%-25% подозрение на плагиат' + '\r\n'
        outText += '50%-75% средняя уникальность, 75%-100% высокая уникальность' + '\r\n' + '\r\n'
        outText += 'ОбЩАЯ УНИКАЛЬНОСТЬ: {0}%'.format(res[0]) + '\r\n' + '\r\n'
        if len(res[1].keys()) > 0:
            outText += 'НАИБОЛЕЕ ПОХОЖИЕ ИСТОЧНИКИ:' + '\r\n'+ '\r\n'
            for K in res[1].keys():
                outText +='ИМЯ: {0}\r\nУНИКАЛЬНОСТЬ: {1}%\r\nСАЙТ: {2}\r\nТЕКСТ: {3}\r\n\r\n'.format(K, res[1][K][0], res[1][K][1],res[1][K][2])
    return outText


def ScienceHelperBot():
    TOKEN = os.environ['TOKEN']
    updater = Updater(token=TOKEN)  # Токен API к Telegram
    dispatcher = updater.dispatcher

    # Обработка команд
    def startCommand(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='добро пожаловать, {name}, в гости к Виртуальному помощнику ученого! В настоящее время работает проверка на антиплагиат! Отправьте текст на английском или русском языке'.format(
                             name=update.message.from_user.first_name))

    def textMessage(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Ожидайте! Идет анализ текста на плагиат. Может занять некоторое время (зависит от размера текста)')
        res = FindPlagiatTelegramm(update.message.text, 3)
        bot.send_message(chat_id=update.message.chat_id, text=res)
        time.sleep(3)

    # Хендлеры
    start_command_handler = CommandHandler('start', startCommand)
    text_message_handler = MessageHandler(Filters.text, textMessage)
    # Добавляем хендлеры в диспетчер
    dispatcher.add_handler(start_command_handler)
    dispatcher.add_handler(text_message_handler)
    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    updater.idle()

    return True

while True:
    try:
        ScienceHelperBot()
    except:
        print('Перезапуск бота')




