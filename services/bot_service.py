#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram VIP会员机器人服务

该模块提供Telegram机器人的核心功能，包括：
- VIP会员订阅管理
- 支付处理
- 邮件通知
- 定时消息推送
"""

# 导入标准库
import sqlite3
import ssl
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 导入第三方库
from telegram import LabeledPrice, Update
from telegram.ext import (
    Updater, CommandHandler, CallbackContext,
    PreCheckoutQueryHandler, MessageHandler, filters
)
from apscheduler.schedulers.background import BackgroundScheduler


# ===== 邮件服务功能 =====

def send_email(subject, body, to_email):
    """
    发送邮件通知

    参数:
        subject (str): 邮件主题
        body (str): 邮件正文
        to_email (str): 收件人邮箱

    说明:
        使用SMTP_SSL连接Gmail服务器发送邮件
        实际应用中应从配置文件读取邮箱凭据
    """
    sender_email = "your_email@example.com"  # 应从配置文件读取
    receiver_email = to_email
    password = "your_email_password"  # 应从配置文件读取，不应硬编码

    # 创建邮件对象
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # 添加邮件正文
    message.attach(MIMEText(body, "plain"))

    # 发送邮件
    ssl_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"邮件已发送至 {to_email}")


# ===== 数据库操作功能 =====

def update_user_subscription(user_id, duration_months=1):
    """
    更新用户的VIP订阅状态

    参数:
        user_id (int): 用户ID
        duration_months (int): 订阅时长（月），默认为1个月

    说明:
        计算订阅到期日期并更新数据库
        使用INSERT OR REPLACE确保记录存在时更新，不存在时插入
    """
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    # 计算到期日期（每月按30天计算）
    expiration_date = datetime.now() + timedelta(days=30 * duration_months)

    # 更新数据库
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, is_vip, vip_expiration_date)
    VALUES (?, 1, ?)
    ''', (user_id, expiration_date.strftime('%Y-%m-%d')))

    conn.commit()
    conn.close()


def check_vip_status(user_id):
    """
    检查用户的VIP状态

    参数:
        user_id (int): 用户ID

    返回:
        bool: 用户是否为有效VIP会员

    说明:
        查询数据库判断用户是否为VIP会员且未过期
    """
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    # 查询用户VIP状态
    cursor.execute('SELECT is_vip, vip_expiration_date FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        is_vip, expiration_date = user
        if is_vip:
            # 检查是否过期
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            if expiration_date < datetime.now():
                return False
            else:
                return True
        else:
            return False
    else:
        return False


# ===== 支付处理功能 =====

def pay(update: Update, context: CallbackContext) -> None:
    """
    处理用户的订阅支付请求

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        根据用户选择的订阅类型（月度/年度）发送支付请求
        使用Telegram的支付API创建支付发票
    """
    # 获取订阅类型参数
    subscription_type = context.args[0]

    # 根据订阅类型设置价格和时长
    if subscription_type == "monthly":
        prices = [LabeledPrice('VIP 订阅月费', 1000)]  # 10.00 USD
        duration_months = 1
    elif subscription_type == "yearly":
        prices = [LabeledPrice('VIP 订阅年费', 10000)]  # 100.00 USD
        duration_months = 12
    else:
        update.message.reply_text('无效的订阅类型。')
        return

    # 发送支付请求
    context.bot.send_invoice(
        chat_id=update.message.chat_id,
        title="VIP 订阅",
        description=f"按{subscription_type}订阅VIP会员",
        payload="VIP_SUBSCRIPTION",
        provider_token="YOUR_PAYMENT_PROVIDER_TOKEN",  # 应从配置文件读取
        start_parameter="vip_subs",
        currency="USD",
        prices=prices
    )


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """
    支付前检查回调函数

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        验证支付请求的有效性
        必须实现此函数，否则支付会失败
    """
    query = update.pre_checkout_query

    # 验证支付负载是否正确
    if query.invoice_payload != 'VIP_SUBSCRIPTION':
        query.answer(ok=False)
    else:
        query.answer(ok=True)


def successful_payment(update: Update, context: CallbackContext) -> None:
    """
    支付成功后的回调函数

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        处理支付成功后的操作，包括：
        1. 更新用户的VIP状态
        2. 发送确认消息
        3. 发送邮件通知
    """
    user_id = update.message.from_user.id
    subscription_type = update.message.successful_payment.invoice_payload

    # 处理VIP订阅
    if subscription_type == "VIP_SUBSCRIPTION":
        # 根据消息内容判断订阅类型
        if "monthly" in update.message.text.lower():
            update_user_subscription(user_id, duration_months=1)
        elif "yearly" in update.message.text.lower():
            update_user_subscription(user_id, duration_months=12)

    # 发送确认消息
    update.message.reply_text('支付成功！你已成为VIP会员。')

    # 发送邮件通知
    # 注意：这里假设用户对象有email属性，实际应用中需要确认
    send_email("VIP 订阅支付成功", "恭喜！您已成功订阅VIP会员。", update.message.from_user.email)


def unsubscribe(update: Update, context: CallbackContext) -> None:
    """
    处理用户取消订阅请求

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        将用户的VIP状态设为非VIP，并清除到期日期
    """
    user_id = update.message.from_user.id

    # 更新数据库，取消VIP状态
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users SET is_vip = 0, vip_expiration_date = NULL WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

    # 发送确认消息
    update.message.reply_text("您已成功取消VIP订阅。")

    # 发送邮件通知
    send_email("VIP 订阅取消", "您的VIP订阅已被取消。如果有任何问题，请联系我们。", update.message.from_user.email)


# ===== 消息发送功能 =====

def send_purchase_confirmation(update: Update, context: CallbackContext):
    """
    发送购买确认消息

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        根据用户的VIP状态发送不同的确认消息
    """
    user_id = update.message.from_user.id

    # 根据VIP状态发送不同消息
    if check_vip_status(user_id):
        context.bot.send_message(
            chat_id=user_id,
            text="感谢您的购买！您已获得VIP会员福利，享受专属优惠！"
        )
    else:
        context.bot.send_message(
            chat_id=user_id,
            text="感谢您的购买！成为VIP会员可享受更多福利！"
        )


def send_message_to_vip_users(bot, message: str):
    """
    向所有VIP用户发送消息

    参数:
        bot: Telegram机器人实例
        message (str): 要发送的消息内容

    说明:
        查询数据库获取所有VIP用户，并向他们发送指定消息
    """
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    # 查找所有VIP用户
    cursor.execute('SELECT user_id FROM users WHERE is_vip = 1')
    vip_users = cursor.fetchall()

    # 向每个VIP用户发送消息
    for user in vip_users:
        user_id = user[0]
        bot.send_message(chat_id=user_id, text=message)

    conn.close()


def send_special_offer(update: Update, context: CallbackContext):
    """
    发送特别优惠消息给所有VIP用户

    参数:
        update (Update): Telegram更新对象
        context (CallbackContext): 回调上下文

    说明:
        向所有VIP用户发送特别优惠消息，并向发送命令的用户返回确认
    """
    message = "尊敬的VIP用户，感谢您的支持！我们为您提供了一个特别优惠，请不要错过！"
    send_message_to_vip_users(context.bot, message)
    update.message.reply_text("已为所有VIP用户发送特别优惠消息。")


# ===== 定时任务功能 =====

def setup_scheduler(bot):
    """
    设置定时任务调度器

    参数:
        bot: Telegram机器人实例

    说明:
        创建并启动后台调度器，设置定期执行的任务
    """
    # 创建定时任务函数的闭包，确保能够访问bot实例
    def scheduled_monthly_offer():
        message = "尊敬的VIP用户，欢迎来到本月的特别优惠！请查看我们的最新产品和服务。"
        send_message_to_vip_users(bot, message)

    # 创建并启动调度器
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_monthly_offer, 'interval', months=1)  # 每月发送一次
    scheduler.start()

    return scheduler


# ===== 主函数 =====

def main():
    """
    机器人主函数

    说明:
        初始化机器人，注册命令处理器，启动轮询
        设置定时任务调度器
    """
    # 创建Updater实例
    updater = Updater("YOUR_BOT_TOKEN")  # 应从配置文件读取
    dispatcher = updater.dispatcher
    bot = updater.bot

    # 注册命令处理器
    dispatcher.add_handler(
        CommandHandler("start", lambda update, context: update.message.reply_text("欢迎！使用 /pay 命令支付订阅")))
    dispatcher.add_handler(CommandHandler("pay", pay))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(filters.successful_payment, successful_payment))
    dispatcher.add_handler(CommandHandler("purchase", send_purchase_confirmation))
    dispatcher.add_handler(CommandHandler("special_offer", send_special_offer))

    # 设置定时任务调度器
    scheduler = setup_scheduler(bot)

    # 启动机器人
    updater.start_polling()
    updater.idle()

    # 关闭调度器
    scheduler.shutdown()


if __name__ == '__main__':
    main()

# ===== API参数说明 =====
#
# send_invoice() 参数解释：
#
# payload：你自定义的订单标识符，用于验证支付结果。
# provider_token：从 @BotFather 获取的支付令牌。
# prices：LabeledPrice 列表，金额单位是 分（5.00 USD = 500 分）。
# need_email、need_phone_number：可选字段，用于收集用户信息。
#
# precheckout_callback()：支付前检查（必须实现，否则支付失败）。
# successful_payment()：支付成功后触发。
#
# ===== 使用说明 =====
#
# 1. 从BotFather获取机器人令牌和支付提供商令牌
# 2. 更新配置文件中的令牌和邮箱凭据
# 3. 确保数据库表结构正确创建
# 4. 启动机器人服务
# 5. 用户可通过以下命令与机器人交互：
#    - /start: 显示欢迎消息
#    - /pay monthly|yearly: 订阅VIP会员
#    - /unsubscribe: 取消VIP订阅
#    - /purchase: 获取购买确认
#    - /special_offer: 向VIP用户发送特别优惠
