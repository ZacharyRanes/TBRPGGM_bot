#Author: Zachary Ranes
#Written in Python 2.7, requires eternnoir/pyTelegramBotAPI to run

import ConfigParser
import telebot
from telebot import types
import requests

#This loads a config file that holds the bots API key
config = ConfigParser.ConfigParser()
config.read("TBRPGGM_bot_bot_config.cfg")
token = config.get("telegram_bot_api","telegram_token")

#The bot object is the go between the telegram API and the python code
bot = telebot.TeleBot(token)

#Dictionaries 
#key is a chat id holds an message id (message waiting to be replied to)
waiting = {}


#Help command will display the instruction file to the chat 
@bot.message_handler(commands=['help'])
def command_help(message):
    with open("TBRPGGM_instructions.txt", "rb") as instructions:
        bot.reply_to(message, instructions.read()) 

#Gives the option to start playing a game or upload one
@bot.message_handler(commands=['start'])
def command_start(message):
    bot.reply_to(message, "To start /new_adventure use this command\n"\
                            "To /upload_adventure use this command\n"\
                            "For /help with with adventure formating use this command")

#Prompts for a reply of an adventure file and preps for upload_reply_handler
@bot.message_handler(commands=['upload_adventure'])
def command_upload_adventure(message):
    reply = bot.reply_to(message, "Please replay to this message with an adventure file")
    key = message.chat.id
    waiting[key] = reply.message_id

#Helper fuction for upload_reply_handler
def text_test(message):
	return message.document.mime_type == 'text/plain'

#
@bot.message_handler(func=text_test, content_types=['document'])
def upload_reply_handler(message):
    key = message.chat.id
    if key in waiting:
        if message.reply_to_message.message_id == waiting[key]:
            waiting.pop(key, None)
            reply = bot.reply_to(message, "Reading file...")
            file_parser(reply.message_id, message.document.file_id)

#
def file_parser(message_id, file_id):
    file_info = bot.get_file(file_id)
    adventure_file = bot.download_file(file_info.file_path)
    #adventure_file pass this object to the parser part of the project 


bot.polling()