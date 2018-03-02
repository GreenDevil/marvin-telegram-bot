# -*- coding: utf-8 -*-

import json
import locale
import sys
from xml.etree import cElementTree

import apiai
import requests
import telegram
from bs4 import BeautifulSoup
# Настройки
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import config

updater = Updater(token=config.telegram_token)  # Токен API к Telegram bot MarvinMiniBot

dispatcher = updater.dispatcher

# phrases = json.load(open('phrases.json'))
# phrases_messages = []
# for i in range(len(phrases)):
#     message_text = phrases[i]["message"].lower()
#     phrases_messages.append(message_text)
#
if sys.platform == 'win32':
    locale.setlocale(locale.LC_ALL, 'rus_rus')
else:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


# Обработчик команд
def startCommand(bot, update):
    pass


def habrahabrTop3(bot, update):
    news = parse_habrahabr_rss()
    for i in range(len(news)):
        text_msg = news[i].get('title') + "\n" + news[i].get('link') + "\n"
        bot.send_message(chat_id=update.message.chat_id, text=text_msg)


def parse_habrahabr_rss():
    """Парсинг 3 новостей топа с https://habrahabr.ru/rss/best/
    """
    response = requests.get('https://habrahabr.ru/rss/best/')
    parsed_xml = cElementTree.fromstring(response.content)
    items = []
    for node in parsed_xml.iter():
        if node.tag == 'item':
            item = {}
            for item_node in list(node):
                if item_node.tag == 'title':
                    item['title'] = item_node.text
                if item_node.tag == 'link':
                    item['link'] = item_node.text
            items.append(item)
    return items[:3]


def meme_get(bot, update):
    memes = requests.get('https://www.memecenter.com/')
    soup = BeautifulSoup(memes.content, "html.parser")
    memes_img = (soup.find("a", class_="random"))
    meme_random = requests.get(memes_img['href'])
    soup_rand = BeautifulSoup(meme_random.content, "html.parser")

    random_memes_pic = soup_rand.find_all("img", class_="rrcont")
    random_memes_vid = soup_rand.find_all("source", type="video/mp4")
    if random_memes_pic is not None and len(random_memes_pic) > 0:
        random_memes_pic_src = random_memes_pic[0]['src']
        bot.send_message(chat_id=update.message.chat_id, text=random_memes_pic_src)
    elif random_memes_vid is not None and len(random_memes_vid) > 0:
        random_memes_vid_src = random_memes_vid[0]['src']
        bot.send_message(chat_id=update.message.chat_id, text=random_memes_vid_src)


def textMessage(bot, update):
    # if update.message.text == "мем":    Для поиска по тексту сообщения
    request = apiai.ApiAI(config.dialogflow_token).text_request()  # Токен API к Dialogflow
    request.lang = 'ru'  # На каком языке будет послан запрос
    request.session_id = 'MarvinAIBot'  # ID Сессии диалога (нужно, чтобы потом учить бота)
    message_text = update.message.text.replace('@MarvinMiniBot', '')
    request.query = message_text  # Посылаем запрос к ИИ с сообщением от юзера
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))  # Ответ json в формате utf-8
    if responseJson.get('result').get('resolvedQuery') == 'Хватит':  # TODO сделать нормальную обработку команды остановки показа мемов, в условии с мемами
        reply_markup = telegram.ReplyKeyboardRemove()
        bot.sendMessage(chat_id=update.message.chat_id, text="Окай", reply_markup=reply_markup)
    elif responseJson.get('result').get('metadata').get('intentName') == 'habrahabr.top':  # Показ 3 лучших стстей с хабра за сегодня
        habrahabrTop3(bot, update)
    elif responseJson.get('result').get('metadata').get('intentName') == 'memes':  # Показ рандомного мема с memecenter.com
        meme_get(bot, update)
        bot.sendMessage(chat_id=update.message.chat_id, text="Показать ещё?",
                        # reply_markup={"keyboard": [["Ещё мем"], ["Хватит"]], "resize_keyboard": True})
                        reply_markup={"keyboard": [["Ещё мем", "Хватит"]], "resize_keyboard": True, "selective": True})
    else:  # тандартный ответ с помощью dialogflow
        response = responseJson['result']['fulfillment']['speech']  # Разбираем JSON и вытаскиваем ответ
        # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
        if response:
            bot.send_message(chat_id=update.message.chat_id, text=response)


# Хендлеры
start_command_handler = CommandHandler('start', startCommand)
habrahabr_command_handler = CommandHandler('habrahabra_top3', habrahabrTop3)
text_message_handler = MessageHandler(Filters.text, textMessage)
# Диспетчеры
dispatcher.add_handler(start_command_handler)
dispatcher.add_handler(habrahabr_command_handler)
dispatcher.add_handler(text_message_handler)

# # Обработчик сообщений, подходящих под указанное регулярное выражение
# @bot.message_handler(regexp="past something regex phrase here")
# def handle_message(message):
#     pass
#
#
#  # Обработчик для документов и аудиофайлов
# @bot.message_handler(content_types=['document', 'audio'])
# def handle_docs_audio(message):
#     pass


if __name__ == '__main__':
    updater.start_polling(clean=True)
