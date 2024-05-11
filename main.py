import threading

import config
from bs4 import BeautifulSoup as BS
from Classes.User import UserAgent
import requests
import telebot
import sqlite3
import time

st_accept = "text/html"
st_useragent = UserAgent().get_useragent()

headers = {
    "Accept": st_accept,
    "User-Agent": st_useragent
}


def get_weather():
    req = requests.get('https://pogoda1.ru/moscow/rayon-zamoskvoreche/', headers)
    class_ = 'row-forecast-time-of-day'

    html = BS(req.text, 'html.parser')
    result = html.find(class_=class_).text

    result = result.split('\n')

    message = (f'Погода зараз:\n'
               f'На вулиці: {result[4]}.\n'
               f'Температура: {result[6]} градусів.\n'
               f'Швидкість вітру: {result[10]}.\n'
               f'Вологість: {result[14]}.\n'
               f'Опади: {result[15]}.')

    return message


def get_news():
    req = requests.get('https://zamos.ru/news/', headers)
    class_ = 'af-t-anons'

    html = BS(req.text, 'html.parser')
    result = html.find(class_=class_).find('h4').text
    result = (f"Назва: {result}\n"
              f"Опис: {html.find(class_=class_).find(class_='caption').text}")

    return result


token = config.TOKEN
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    data = cursor.fetchone()

    if data is None:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()


def send_messages():
    old_news = ''

    while True:
        weather = get_weather()
        news = get_news()

        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users")
        user_ids = cursor.fetchall()
        conn.close()

        for user_id in user_ids:
            try:
                if news != old_news:
                    bot.send_message(user_id[0], f"Новини района: {news}\n")
                    old_news = news

                bot.send_message(user_id[0], weather)
            except Exception as e:
                conn = sqlite3.connect('bot.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id[0],))
                conn.commit()
                conn.close()

            time.sleep(1800)


message_thread = threading.Thread(target=send_messages)
message_thread.start()

bot.polling()
