#!/bin/python3

import telebot as tb
import uuid
import os
from dotenv import load_dotenv
import pymongo as pm
from kandinsky import Text2ImageAPI
from gigachatapi import GigaChatAPI
import base64

load_dotenv()

GIGACHAT_AUTH_TOKEN = os.getenv('GIGACHAT_AUTH_TOKEN')
BOT_TOKEN = os.getenv('BOT_TOKEN')

def connect_mongo():
  MONGO_HOST = os.getenv('MONGO_HOST')
  MONGO_DB = os.getenv('MONGO_DB')
  MONGO_USER = os.getenv('MONGO_USER')
  MONGO_PASS = os.getenv('MONGO_PASS')
  client = pm.MongoClient(MONGO_HOST, username=MONGO_USER, password=MONGO_PASS)
  return client[MONGO_DB]

gigachat = GigaChatAPI(GIGACHAT_AUTH_TOKEN)
gigachat.login()
bot = tb.TeleBot(BOT_TOKEN)
db = connect_mongo()
collection = db[os.getenv('MONGO_COLLECTION')]

bot.set_my_commands([
    tb.types.BotCommand("/start", "main menu"),
    tb.types.BotCommand("/reset", "Удалить историю чата"),
    tb.types.BotCommand("/chat", "переключает в режим чата"),
    tb.types.BotCommand("/image", "переключает в режим генерации картинок")
])

@bot.message_handler(commands=['start'])
def send_welcome(message):
  uid = str(message.from_user.id)
  bot.reply_to(message, "тещщу api гигачата")

  cursor = collection.find({"_id": uid})
  if len(list(cursor)) == 0:
    collection.insert_one({"_id": uid, "mode": 1, "messages": []})

@bot.message_handler(commands=['reset'])
def reset_dialogue(message):
  uid = str(message.from_user.id)
  if list(collection.find({"_id": uid})) != 0:
    collection.update_one({'_id': uid}, {'$set': {"mode": 1, "messages": []}})

@bot.message_handler(commands=['chat'])
def switch_to_chat(message):
  uid = str(message.from_user.id)
  if list(collection.find({"_id": uid})) != 0:
    collection.update_one({'_id': uid}, {'$set': {"mode": 1}})

@bot.message_handler(commands=['image'])
def switch_to_text2image(message):
  uid = str(message.from_user.id)
  if list(collection.find({"_id": uid})) != 0:
    collection.update_one({'_id': uid}, {'$set': {"mode": 2}})
     
@bot.message_handler(func=lambda m: True)
def process_prompt(message):
  uid = str(message.from_user.id)
  user_record = {"role": "user", "content": message.text}

  cursor = collection.find({"_id": uid})

  if len(list(cursor)) == 0:
    collection.insert_one({"_id": uid, "mode": 1, "messages": []})

  cursor = collection.find({"_id": uid})
  mode = cursor[0]['mode']

  if mode == 1:
    messages = cursor[0]['messages']
    messages.append(user_record)
    answer = gigachat.chat(messages)
    bot_record = {"role": "assistant", "content": answer}
    messages.append(bot_record)
    collection.update_one({'_id': uid}, {'$set': {"messages": messages}})

    bot.reply_to(message, answer)
  elif mode == 2:
    path = f'./files/{str(uuid.uuid4())}.jpg'
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', os.getenv('KAND_API'), os.getenv('KAND_KEY'))
    model_id = api.get_model()
    kuuid = api.generate(message.text, model_id)
    image = base64.b64decode(api.check_generation(kuuid)[0])
    with open(path, '+bw') as file:
      file.write(image)
    with open(path, 'rb') as file:
      bot.send_photo(message.chat.id, file)

bot.infinity_polling()
							