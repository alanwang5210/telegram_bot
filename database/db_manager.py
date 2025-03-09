# 数据库管理器

import json

from database.models import get_db_connection, init_database

from Crypto.Random import get_random_bytes
import base64


class DatabaseManager:
    """
    数据库管理器类，提供数据库操作的高级接口
    """

    @staticmethod
    def initialize_database():
        """
        初始化数据库表结构
        """
        try:
            init_database()
            return True
        except Exception as e:
            print(f"初始化数据库失败: {e}")
            return False

    @staticmethod
    def execute_query(query, params=None, fetch_one=False):
        """
        执行SQL查询
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        return cursor.fetchone()
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid if cursor.lastrowid else True
        except Exception as e:
            if not query.strip().upper().startswith('SELECT'):
                conn.rollback()
            print(f"执行查询失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all_users(is_vip=None):
        """
        获取所有用户，可选择只获取VIP用户
        """
        query = "SELECT * FROM users"
        params = []

        if is_vip is not None:
            query += " WHERE is_vip = %s"
            params.append(is_vip)

        return DatabaseManager.execute_query(query, params)

    @staticmethod
    def get_user_by_id(user_id):
        """
        通过ID获取用户
        """
        query = "SELECT * FROM users WHERE id = %s"
        return DatabaseManager.execute_query(query, (user_id,), fetch_one=True)

    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        """
        通过Telegram ID获取用户
        """
        query = "SELECT * FROM users WHERE telegram_id = %s"
        return DatabaseManager.execute_query(query, (telegram_id,), fetch_one=True)

    @staticmethod
    def create_card_key(plan_type, count=1):
        """
        生成卡密
        """
        conn = get_db_connection()
        try:
            created_keys = []
            with conn.cursor() as cursor:
                for _ in range(count):
                    # 生成随机卡密
                    random_bytes = get_random_bytes(16)
                    card_key = base64.b64encode(random_bytes).decode('utf-8')[:20]
                    card_key = ''.join(c for c in card_key if c.isalnum())  # 确保只包含字母和数字

                    # 插入数据库
                    cursor.execute(
                        "INSERT INTO card_keys (card_key, plan_type) VALUES (%s, %s)",
                        (card_key, plan_type)
                    )
                    created_keys.append({
                        'id': cursor.lastrowid,
                        'card_key': card_key,
                        'plan_type': plan_type
                    })
            conn.commit()
            return created_keys
        except Exception as e:
            conn.rollback()
            print(f"创建卡密失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def use_card_key(card_key, user_id):
        """
        使用卡密
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查卡密是否存在且未使用
                cursor.execute(
                    "SELECT * FROM card_keys WHERE card_key = %s AND is_used = FALSE",
                    (card_key,)
                )
                card = cursor.fetchone()

                if not card:
                    return None

                # 标记卡密为已使用
                cursor.execute(
                    """UPDATE card_keys 
                    SET is_used = TRUE, used_by = %s, used_at = NOW() 
                    WHERE id = %s""",
                    (user_id, card['id'])
                )

                conn.commit()
                return card
        except Exception as e:
            conn.rollback()
            print(f"使用卡密失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def create_payment(user_id, payment_type, amount, currency='CNY', subscription_id=None, payment_data=None):
        """
        创建支付记录
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO payments 
                    (user_id, subscription_id, payment_type, amount, currency, payment_data) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, subscription_id, payment_type, amount, currency,
                     json.dumps(payment_data) if payment_data else None)
                )
                payment_id = cursor.lastrowid
                conn.commit()
                return payment_id
        except Exception as e:
            conn.rollback()
            print(f"创建支付记录失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_payment_status(payment_id, status, transaction_id=None, payment_data=None):
        """
        更新支付状态
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                update_fields = ["status = %s"]
                params = [status]

                if transaction_id:
                    update_fields.append("transaction_id = %s")
                    params.append(transaction_id)

                if payment_data:
                    update_fields.append("payment_data = JSON_MERGE_PATCH(IFNULL(payment_data, '{}'), %s)")
                    params.append(json.dumps(payment_data))

                params.append(payment_id)

                query = f"""UPDATE payments 
                SET {', '.join(update_fields)} 
                WHERE id = %s"""

                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"更新支付状态失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def create_message(title, content, is_vip_only=True, created_by=None):
        """
        创建消息
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO messages 
                    (title, content, is_vip_only, created_by) 
                    VALUES (%s, %s, %s, %s)""",
                    (title, content, is_vip_only, created_by)
                )
                message_id = cursor.lastrowid
                conn.commit()
                return message_id
        except Exception as e:
            conn.rollback()
            print(f"创建消息失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def send_message_to_users(message_id, user_ids=None):
        """
        发送消息给用户
        如果user_ids为None，则发送给所有用户
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 获取消息信息
                cursor.execute(
                    "SELECT * FROM messages WHERE id = %s",
                    (message_id,)
                )
                message = cursor.fetchone()

                if not message:
                    return False

                # 确定接收用户
                if user_ids is None:
                    # 如果是VIP专属消息，只发送给VIP用户
                    if message['is_vip_only']:
                        cursor.execute("SELECT id FROM users WHERE is_vip = TRUE")
                    else:
                        cursor.execute("SELECT id FROM users")

                    users = cursor.fetchall()
                    user_ids = [user['id'] for user in users]

                # 批量插入消息发送记录
                values = []
                for user_id in user_ids:
                    values.append((message_id, user_id))

                if values:
                    cursor.executemany(
                        """INSERT IGNORE INTO message_deliveries 
                        (message_id, user_id) VALUES (%s, %s)""",
                        values
                    )

                conn.commit()
                return len(values)
        except Exception as e:
            conn.rollback()
            print(f"发送消息失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def create_notification(user_id, notification_type, title, content, is_email=False, is_telegram=True):
        """
        创建通知
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO notifications 
                    (user_id, type, title, content, is_email, is_telegram) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, notification_type, title, content, is_email, is_telegram)
                )
                notification_id = cursor.lastrowid
                conn.commit()
                return notification_id
        except Exception as e:
            conn.rollback()
            print(f"创建通知失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def mark_notification_sent(notification_id):
        """
        标记通知为已发送
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE notifications 
                    SET is_sent = TRUE, sent_at = NOW() 
                    WHERE id = %s""",
                    (notification_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"标记通知失败: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_pending_notifications(is_email=None, is_telegram=None):
        """
        获取待发送的通知
        """
        query = "SELECT * FROM notifications WHERE is_sent = FALSE"
        params = []

        if is_email is not None:
            query += " AND is_email = %s"
            params.append(is_email)

        if is_telegram is not None:
            query += " AND is_telegram = %s"
            params.append(is_telegram)

        return DatabaseManager.execute_query(query, params)
