import schedule
import time
import telebot

BOT_TOKEN = '7828782705:AAEqigD1AUJUTBgObs3t0aUV6L-uFqemgA0'

bot = telebot.TeleBot(token=BOT_TOKEN, parse_mode=None)


def send_message():
    """发送消息到 Telegram"""
    try:
        bot.send_message(chat_id="", text="这是自动发布的消息")
        print("消息发送成功")
    except Exception as e:
        print(f"发送消息失败: {e}")


# 每隔 1 小时执行一次
schedule.every(1).hours.do(send_message)

# 每天中午 12:00 执行一次
schedule.every().day.at("12:00").do(send_message)

# 持续运行
while True:
    schedule.run_pending()  # 执行所有准备好的任务
    time.sleep(1)  # 每秒检查一次
