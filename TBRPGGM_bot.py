#Author: Zachary Ranes
#Written in Python 3, requires eternnoir/pyTelegramBotAPI to run

from configparser import ConfigParser
from telebot import TeleBot
from telebot import types
import requests
import TBRPGGM_parser as parser
import copy
import os


#This loads a config file that holds the bots API key
config = ConfigParser()
config.read("TBRPGGM_config.cfg")
TOKEN = config.get("telegram_bot_api","telegram_token")
bot = TeleBot(TOKEN)

#Loads adventure game files from long term storage on boot startup
def load_files():
    dic = {}
    for filename in os.listdir('adventures/'):
        filepath = 'adventures/'+filename
        dic[filename] = parser.loadAGF(filepath)
    return dic

#key is a chat id holds an message id (message waiting to be replied to)
waiting = {}
#key is original file names holds adventure game objects
adventures = load_files()
#key is chat id hold edited adventure game objects
running_adventures = {}

#Help command will display the instruction file to the chat 
@bot.message_handler(commands=['help'])
def command_help(message):
    with open("TBRPGGM_instructions.txt", "rb") as instructions:
        bot.reply_to(message, instructions.read()) 

#Gives the option to start playing a game or upload one
@bot.message_handler(commands=['start'])
def command_start(message):
    bot.reply_to(message, "To start a /new_adventure use this command\n"\
                          "To /upload_adventure use this command\n"\
                          "For /help with with adventure formatting use this command")

#Prompts for a reply of an adventure file and preps for upload_reply_handler
@bot.message_handler(commands=['upload_adventure'])
def command_upload_adventure(message):
    reply = bot.reply_to(message, "Please reply to this message with an adventure file")
    key = message.chat.id
    waiting[key] = reply.message_id

#Reads in files from user responce 
@bot.message_handler(content_types=['document'])
def upload_reply_handler(message):
    key = message.chat.id
    if key in waiting:
        if message.reply_to_message.message_id == waiting[key]:
            waiting.pop(key, None)
            bot.reply_to(message, "Reading/Parsing File")
            try:
                file_info = bot.get_file(message.document.file_id)
                adventure_file = bot.download_file(file_info.file_path)
                name = message.document.file_name
                adventures[name] = parser.parseAGF(adventure_file)
                parser.saveAGF(adventures[name], 'adventures/'+name)
                bot.reply_to(message, "Done")
            except:
                bot.reply_to(message, "Parsing Failed, please read /help for intustions on formating adventure files")

#Shows options of uploaded adventured  
@bot.message_handler(commands=['new_adventure'])
def command_new_adventure(message):
    markup = types.InlineKeyboardMarkup()
    for a in adventures:
        title = adventures[a].adventureTitle()
        markup.row(types.InlineKeyboardButton(callback_data=a,
                                              text=title))
    bot.reply_to(message, "Which adventure do you want to play?", \
                                              reply_markup=markup)

#Handles the callback data sent from the new_adventure command 
@bot.callback_query_handler(func=lambda call:
                call.message.chat.id not in running_adventures and\
                call.data in adventures)
def callback_start_new_adventure(call):
    key = call.message.chat.id
    title = adventures[call.data].adventureTitle()
    bot.edit_message_text("Which adventure do you want to play?\n"\
                           "==> " + title, 
                              message_id=call.message.message_id, 
                              chat_id=key, 
                              reply_markup=None)
    running_adventures[key] = copy.deepcopy(adventures[call.data])
    run_adventure(key)

#Called with the key to the running_adventures dic to show current choices
def run_adventure(key):
    text = running_adventures[key].state()
    choices = running_adventures[key].getChoices()
    markup = types.InlineKeyboardMarkup()
    i = 0
    for ch in choices:
        markup.row(types.InlineKeyboardButton(callback_data="ch"+str(i), text=ch))
        i += 1
    bot.send_message(key, text, reply_markup=markup)
    
    if running_adventures[key].isEnd():
        if running_adventures[key].isWin():
            bot.send_message(key, "BOT: Adventure completed")
            del running_adventures[key]
        else:
            bot.send_message(key, "BOT: Adventure end")
    
#Handles the call back that clicking an inline choice sends
@bot.callback_query_handler(func=lambda call: \
                    call.message.chat.id in running_adventures and\
                    call.data[:2] == "ch")
def choice_handler(call):
    key = call.message.chat.id
    text = running_adventures[key].state()
    choices = running_adventures[key].getChoices()
    i = int(call.data[2:])
    bot.edit_message_text(text + "\n==> " + choices[i], 
                              message_id=call.message.message_id, 
                              chat_id=key, 
                              reply_markup=None)
    running_adventures[key].choose(i)
    run_adventure(key)

if __name__ == '__main__':
    while True:
        #if a network error with Telegram polling will crash 
        try:
            bot.polling(none_stop=True)
        except Exception as ex:
            print(ex)