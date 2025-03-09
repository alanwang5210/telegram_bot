# 通知服务

import datetime
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.db_manager import DatabaseManager
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, TELEGRAM_BOT_TOKEN
from telegram import Bot
from telegram.error import TelegramError


class NotificationService:
    """
    通知服务类，处理通知相关的业务逻辑
    """

    # 初始化Telegram Bot实例
    _bot = None

    @classmethod
    def get_bot(cls):
        """
        获取或创建Telegram Bot实例
        """
        if cls._bot is None:
            cls._bot = Bot(TELEGRAM_BOT_TOKEN)
        return cls._bot

    @staticmethod
    def create_notification(user_id, notification_type, title, content, is_email=False, is_telegram=True):
        """
        创建通知

        参数:
            user_id: 用户ID
            notification_type: 通知类型 ('subscription_expiry', 'payment_success', 'payment_failed', 'system')
            title: 通知标题
            content: 通知内容
            is_email: 是否发送邮件
            is_telegram: 是否发送Telegram消息

        返回:
            (success, notification_id或错误信息)
        """
        try:
            notification_id = DatabaseManager.create_notification(
                user_id, notification_type, title, content, is_email, is_telegram
            )
            return True, notification_id
        except Exception as e:
            print(f"创建通知失败: {e}")
            return False, f"创建通知失败: {str(e)}"

    @staticmethod
    def send_email_notification(notification):
        """
        发送邮件通知

        参数:
            notification: 通知记录

        返回:
            是否成功
        """
        try:
            # 获取用户邮箱
            user = DatabaseManager.get_user_by_id(notification['user_id'])
            if not user or not user['email']:
                print(f"用户 {notification['user_id']} 没有设置邮箱")
                return False

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = user['email']
            msg['Subject'] = notification['title']

            # 添加邮件内容
            msg.attach(MIMEText(notification['content'], 'plain'))

            # 发送邮件
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            # 标记通知为已发送
            DatabaseManager.mark_notification_sent(notification['id'])
            return True
        except Exception as e:
            print(f"发送邮件通知失败: {e}")
            return False

    @staticmethod
    def send_telegram_notification(notification):
        """
        发送Telegram通知

        参数:
            notification: 通知记录

        返回:
            是否成功
        """
        try:
            # 获取用户Telegram ID
            user = DatabaseManager.get_user_by_id(notification['user_id'])
            if not user or not user['telegram_id']:
                print(f"用户 {notification['user_id']} 没有关联Telegram账号")
                return False

            # 准备消息内容
            message = f"*{notification['title']}*\n\n{notification['content']}"

            # 获取Bot实例
            bot = NotificationService.get_bot()

            # 使用python-telegram-bot发送消息
            # 创建一个事件循环来运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 发送消息
                loop.run_until_complete(
                    bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message
                    )
                )

                # 标记通知为已发送
                DatabaseManager.mark_notification_sent(notification['id'])
                return True
            except TelegramError as te:
                print(f"Telegram API错误: {te}")
                return False
            finally:
                loop.close()

        except Exception as e:
            print(f"发送Telegram通知失败: {e}")
            return False

    @staticmethod
    def process_pending_notifications():
        """
        处理所有待发送的通知

        返回:
            (email_sent_count, telegram_sent_count)
        """
        email_sent = 0
        telegram_sent = 0

        try:
            # 处理邮件通知
            email_notifications = DatabaseManager.get_pending_notifications(is_email=True)
            for notification in email_notifications:
                if NotificationService.send_email_notification(notification):
                    email_sent += 1

            # 处理Telegram通知
            telegram_notifications = DatabaseManager.get_pending_notifications(is_telegram=True)
            for notification in telegram_notifications:
                if NotificationService.send_telegram_notification(notification):
                    telegram_sent += 1

            return email_sent, telegram_sent
        except Exception as e:
            print(f"处理待发送通知失败: {e}")
            return email_sent, telegram_sent

    @staticmethod
    def create_payment_success_notification(user_id, payment_info, subscription_info):
        """
        创建支付成功通知

        参数:
            user_id: 用户ID
            payment_info: 支付信息
            subscription_info: 订阅信息

        返回:
            (success, notification_id或错误信息)
        """
        title = "支付成功通知"
        content = f"您的支付已成功处理。\n\n"
        content += f"支付金额: {payment_info['amount']} {payment_info['currency']}\n"
        content += f"支付方式: {payment_info['payment_type']}\n"

        if subscription_info:
            content += f"订阅计划: {subscription_info['plan_name']}\n"
            content += f"有效期至: {subscription_info['end_date'].strftime('%Y-%m-%d %H:%M:%S')}"

        return NotificationService.create_notification(
            user_id, 'payment_success', title, content, is_email=True, is_telegram=True
        )

    @staticmethod
    def create_payment_failed_notification(user_id, payment_info, error_message):
        """
        创建支付失败通知

        参数:
            user_id: 用户ID
            payment_info: 支付信息
            error_message: 错误信息

        返回:
            (success, notification_id或错误信息)
        """
        title = "支付失败通知"
        content = f"您的支付处理失败。\n\n"
        content += f"支付金额: {payment_info['amount']} {payment_info['currency']}\n"
        content += f"支付方式: {payment_info['payment_type']}\n"
        content += f"错误信息: {error_message}\n\n"
        content += "请稍后重试或联系客服获取帮助。"

        return NotificationService.create_notification(
            user_id, 'payment_failed', title, content, is_email=True, is_telegram=True
        )

    @staticmethod
    def create_subscription_expiry_notification(user_id, subscription_info, days_before_expiry):
        """
        创建订阅即将到期通知

        参数:
            user_id: 用户ID
            subscription_info: 订阅信息
            days_before_expiry: 到期前天数

        返回:
            (success, notification_id或错误信息)
        """
        title = "订阅即将到期提醒"
        content = f"您的{subscription_info['plan_name']}订阅即将到期。\n\n"
        content += f"到期时间: {subscription_info['end_date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"剩余天数: {days_before_expiry}天\n\n"

        if subscription_info['auto_renew']:
            content += "您的订阅已设置为自动续费，将在到期时自动续订。"
        else:
            content += "请及时续费以继续享受VIP服务。"

        return NotificationService.create_notification(
            user_id, 'subscription_expiry', title, content, is_email=True, is_telegram=True
        )

    @staticmethod
    def create_subscription_expired_notification(user_id, subscription_info):
        """
        创建订阅已到期通知

        参数:
            user_id: 用户ID
            subscription_info: 订阅信息

        返回:
            (success, notification_id或错误信息)
        """
        title = "订阅已到期通知"
        content = f"您的{subscription_info['plan_name']}订阅已经到期。\n\n"
        content += f"到期时间: {subscription_info['end_date'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "您将无法继续享受VIP服务，请及时续费。"

        return NotificationService.create_notification(
            user_id, 'subscription_expiry', title, content, is_email=True, is_telegram=True
        )

    @staticmethod
    def create_system_notification(user_id, title, content, is_email=False, is_telegram=True):
        """
        创建系统通知

        参数:
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            is_email: 是否发送邮件
            is_telegram: 是否发送Telegram消息

        返回:
            (success, notification_id或错误信息)
        """
        return NotificationService.create_notification(
            user_id, 'system', title, content, is_email, is_telegram
        )
