# 数据库模型定义

import datetime
import pymysql
import json

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


# 数据库连接初始化
def get_db_connection():
    """
    获取数据库连接
    """

    # 建立数据库连接
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


# 初始化数据库表
def init_database():
    """
    初始化数据库表结构
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 创建用户表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                email VARCHAR(255),
                is_vip BOOLEAN DEFAULT FALSE,
                subscription_end_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_telegram_id (telegram_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建订阅记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan_type VARCHAR(50) NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                auto_renew BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_end_date (end_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建支付记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                subscription_id INT,
                payment_type ENUM('card', 'crypto', 'third_party') NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(10) DEFAULT 'CNY',
                status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
                transaction_id VARCHAR(255),
                payment_data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建卡密表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_keys (
                id INT AUTO_INCREMENT PRIMARY KEY,
                card_key VARCHAR(50) UNIQUE NOT NULL,
                plan_type VARCHAR(50) NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                used_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                used_at DATETIME,
                FOREIGN KEY (used_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_card_key (card_key),
                INDEX idx_is_used (is_used)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建消息表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                is_vip_only BOOLEAN DEFAULT TRUE,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建消息发送记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_deliveries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message_id INT NOT NULL,
                user_id INT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                delivered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_message_user (message_id, user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建通知记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('subscription_expiry', 'payment_success', 'payment_failed', 'system') NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                is_sent BOOLEAN DEFAULT FALSE,
                is_email BOOLEAN DEFAULT FALSE,
                is_telegram BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sent_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_is_sent (is_sent)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# 用户模型类
class User:
    def __init__(self, telegram_id, username=None, first_name=None, last_name=None, email=None):
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_vip = False
        self.subscription_end_date = None

    def save(self):
        """
        保存或更新用户信息
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查用户是否已存在
                cursor.execute(
                    "SELECT id FROM users WHERE telegram_id = %s",
                    (self.telegram_id,)
                )
                user = cursor.fetchone()

                if user:
                    # 更新现有用户
                    cursor.execute(
                        """UPDATE users 
                        SET username = %s, first_name = %s, last_name = %s, email = %s 
                        WHERE telegram_id = %s""",
                        (self.username, self.first_name, self.last_name, self.email, self.telegram_id)
                    )
                    user_id = user['id']
                else:
                    # 创建新用户
                    cursor.execute(
                        """INSERT INTO users 
                        (telegram_id, username, first_name, last_name, email) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (self.telegram_id, self.username, self.first_name, self.last_name, self.email)
                    )
                    user_id = cursor.lastrowid

                conn.commit()
                return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_telegram_id(telegram_id):
        """
        通过Telegram ID获取用户
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def update_vip_status(user_id, is_vip, subscription_end_date=None):
        """
        更新用户VIP状态
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE users 
                    SET is_vip = %s, subscription_end_date = %s 
                    WHERE id = %s""",
                    (is_vip, subscription_end_date, user_id)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


# 订阅模型类
class Subscription:
    def __init__(self, user_id, plan_type, start_date, end_date, auto_renew=False):
        self.user_id = user_id
        self.plan_type = plan_type
        self.start_date = start_date
        self.end_date = end_date
        self.auto_renew = auto_renew
        self.is_active = True

    def save(self):
        """
        保存订阅信息
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO subscriptions 
                    (user_id, plan_type, start_date, end_date, is_active, auto_renew) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (self.user_id, self.plan_type, self.start_date, self.end_date,
                     self.is_active, self.auto_renew)
                )
                subscription_id = cursor.lastrowid
                conn.commit()

                # 更新用户VIP状态
                User.update_vip_status(self.user_id, True, self.end_date)

                return subscription_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_active_by_user_id(user_id):
        """
        获取用户的活跃订阅
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM subscriptions 
                    WHERE user_id = %s AND is_active = TRUE 
                    ORDER BY end_date DESC LIMIT 1""",
                    (user_id,)
                )
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def cancel_subscription(subscription_id):
        """
        取消订阅
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 获取订阅信息
                cursor.execute(
                    "SELECT user_id FROM subscriptions WHERE id = %s",
                    (subscription_id,)
                )
                subscription = cursor.fetchone()

                if not subscription:
                    return False

                # 更新订阅状态
                cursor.execute(
                    """UPDATE subscriptions 
                    SET is_active = FALSE, auto_renew = FALSE 
                    WHERE id = %s""",
                    (subscription_id,)
                )

                # 检查用户是否还有其他活跃订阅
                cursor.execute(
                    """SELECT COUNT(*) as count FROM subscriptions 
                    WHERE user_id = %s AND is_active = TRUE""",
                    (subscription['user_id'],)
                )
                result = cursor.fetchone()

                # 如果没有其他活跃订阅，更新用户VIP状态
                if result['count'] == 0:
                    User.update_vip_status(subscription['user_id'], False, None)

                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_expiring_subscriptions(days=3):
        """
        获取即将到期的订阅（用于发送提醒）
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
                cursor.execute(
                    """SELECT s.*, u.telegram_id, u.email 
                    FROM subscriptions s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE s.is_active = TRUE 
                    AND s.end_date BETWEEN NOW() AND %s""",
                    (expiry_date,)
                )
                return cursor.fetchall()
        finally:
            conn.close()


# 支付模型类
class Payment:
    def __init__(self, user_id, payment_type, amount, currency='CNY', subscription_id=None):
        self.user_id = user_id
        self.payment_type = payment_type
        self.amount = amount
        self.currency = currency
        self.subscription_id = subscription_id
        self.status = 'pending'
        self.transaction_id = None
        self.payment_data = {}

    def save(self):
        """
        保存支付记录
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO payments 
                    (user_id, subscription_id, payment_type, amount, currency, status, transaction_id, payment_data) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (self.user_id, self.subscription_id, self.payment_type, self.amount,
                     self.currency, self.status, self.transaction_id,
                     json.dumps(self.payment_data) if self.payment_data else None)
                )
                payment_id = cursor.lastrowid
                conn.commit()
                return payment_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_telegram_id(telegram_id):
        """
        通过Telegram ID获取用户
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def update_vip_status(user_id, is_vip, subscription_end_date=None):
        """
        更新用户VIP状态
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE users 
                    SET is_vip = %s, subscription_end_date = %s 
                    WHERE id = %s""",
                    (is_vip, subscription_end_date, user_id)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
