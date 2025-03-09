
import time

import requests
import telebot

BOT_TOKEN = '7828782705:AAEqigD1AUJUTBgObs3t0aUV6L-uFqemgA0'

bot = telebot.TeleBot(token=BOT_TOKEN, parse_mode=None)


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    if message.text == '/start':
        bot.reply_to(message, "Howdy, how are you doing?")
        return
    elif message.text == '/hello':
        bot.reply_to(message, "Hello, I'm EchoBot!")
        return
    bot.reply_to(message, "Hi, I'm EchoBot!")


@bot.message_handler(commands=['test'])
def sign_handler(message):
    text = "你的星座是什么?\\n选一个: *Aries*, *Taurus*, *Gemini*, *Cancer,* *Leo*, *Virgo*, *Libra*, *Scorpio*, *Sagittarius*, *Capricorn*, *Aquarius*, and *Pisces*."
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, day_handler)


def day_handler(message):
    sign = message.text
    text = "你想知道哪天的呀？\\n选一个吧: *TODAY*, *TOMORROW*, *YESTERDAY*, 或其他 YYYY-MM-DD 格式的日期。"
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, fetch_horoscope, sign.capitalize())


def fetch_horoscope(message, sign):
    day = message.text
    horoscope = get_daily_horoscope(sign, day)
    data = horoscope["data"]
    horoscope_message = f'*运势:* {data["horoscope_data"]}\\n*星座:* {sign}\\n*日期:* {data["date"]}'
    bot.send_message(message.chat.id, "你的运势来啦!")
    bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")


def get_daily_horoscope(sign: str, day: str) -> dict:
    """通过特定的星座获取运势。

    关键字解释:
    sign:str - 星座
    day:str - 格式化的日期 (YYYY-MM-DD) 或 TODAY 或 TOMORROW 或 YESTERDAY
    Return:dict - JSON data
    """
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params)

    return response.json()


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


# Handles all sent documents and audio files
@bot.message_handler(content_types=['document', 'audio', 'photo'])
def handle_docs_audio(message):
    print(message)
    pass


# Handles all text messages that match the regular expression
@bot.message_handler(regexp="SOME_REGEXP")
def handle_message(message):
    pass


bot.infinity_polling()
