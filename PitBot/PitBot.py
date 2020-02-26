import telebot
import json
from datetime import datetime, date, time
import threading
import time

# базовые настройки в коде
token = '790646423:AAEeiyXM7a-5ONsX7CkZnBKK-HJBerM45gU'
settingsfile = 'c:\\temp\\settings.json'
refreshinterval = 600

# инициазиция глобальных переменных
bot = telebot.TeleBot(token)
diclist = []
activechatlist = []

# Прием сообщений бота
@bot.message_handler(content_types=['text'])
def process_messages(message): 
    global activechatlist
    if isadmin(message.chat.id) == True:
        msgtext = message.text
        if msgtext[0:3] == 'add' or msgtext[0:3] == 'Add':
            params = msgtext.split() 
            person = findperson(int(params[1]))
            if person == {}:
                bot.send_message(message.chat.id, 'Такой пользователь не найден')
            else:
                person['expire'] = params[2]
                person['active'] = True
                saveuserlist()
                bot.send_message(message.chat.id, 'Данные пользователя успешно обновлены')
        else:
            if activechatlist:
                for id in activechatlist:
                    bot.send_message(id, msgtext)
                    checknotification(id)
    else:
        person = findperson(message.chat.id)
        if person == {}:
            dic = {'chatid': message.chat.id,
                   'userid': message.from_user.id,
	               'username': message.from_user.username,
	               'active': False,
	               'admin': False,
	               'expire': '01.01.1900'}
            diclist.append(dic)
            sendtoadmin(dic)
            bot.send_message(message.chat.id, 'Здравствуйте. Вы новый пользователь сервиса. Учетные данные зарегестрированы. Теперь администратор может зарегистрировать вас.')
            saveuserlist()
        else:
            accountstatus = 'не активен'
            expiredate = 'не определена'
            
            if person['active']  == True:
                accountstatus = 'активен'
            
            if not person['expire'] == '01.01.1900':
                expiredate = person['expire'] 
            
            bot.send_message(message.chat.id, 'Вы найдены в БД, статус аккаунта: ' + accountstatus + ', дата прекращения действия: ' + expiredate)
            
            if person['active']  == False:
                bot.send_message(message.chat.id, 'Ваш аккаунт не активен. Обратитесь к администратору для активации.')
            
            bot.send_message(message.chat.id, 'данный бот предназначен только для отправки вам сообщений.')

def checknotification(id):
    for dic in diclist:
        if dic['userid'] == id:
            duration = datetime.strptime(dic['expire'], '%d.%m.%Y') - datetime.now()
            seconds = duration.total_seconds() 
            if seconds < 86400:
                 bot.send_message(dic['chatid'], 'Через сутки ваш аккаунт будет отключен! Если хотите продлить - обратитесь к администратору.')

def sendtoadmin(dic):
    for admdic in diclist:
        if admdic['admin'] == True:
             bot.send_message(admdic['chatid'], 'Новый пользователь сервиса! Id: ' + dic['id'] + ', name: ' + dic['username'])    
# проверяем администратор это или нет    
def isadmin(id):
    for dic in diclist:
        if dic['userid'] == id:
            return dic['admin']

# ищет пользователя по имени        
def findperson(name):
    founddic = {}
    for dic in diclist:
        if dic['username'] == name or dic['userid'] == name:
            founddic = dic
    return founddic

# загружает список пользоватеплей из файла
def loaduserlist():
    global diclist
    global activechatlist
    activechatlist = []
    with open(settingsfile) as f: 
        diclist = json.load(f)
    modified = False
    for dic in diclist:
        if dic['active'] == True:
            if datetime.now() < datetime.strptime(dic['expire'], '%d.%m.%Y'):
                activechatlist.append(dic['chatid'])
            else:
                bot.send_message(dic['chatid'], 'Ваш аккаунт был деактивирован! Обратитесь к администратору для продления доуступа.')
                dic['active'] = False
                modified = True
    if modified == True:
        saveuserlist()

# Сохраняет пользователей в файл
def saveuserlist():
    with open(settingsfile, 'w') as f: 
        json.dump(diclist, f) 
        
# обновление списка пользователей
def refresh_userlist():
    while True:
        time.sleep(refreshinterval)
        loaduserlist()
        
################### КОД ОСНОВНОЙ ПРОГРАММЫ #########################################################

loaduserlist()

refreshuserlist_thread = threading.Thread(target=refresh_userlist, name="Refresh userlist", args=(), daemon=True)
refreshuserlist_thread.start()

bot.polling(none_stop=True)