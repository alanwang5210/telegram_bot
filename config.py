# 主配置文件

import os
import yaml

# 加载YAML配置文件
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config-dev.yaml')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 加载配置
config_data = load_config()

# Bot配置
BOT_TOKEN = config_data['bot']['token']
BOT_USERNAME = config_data['bot']['username']
ADMIN_USER_IDS = config_data['bot']['admin_user_ids']

# 数据库配置
DB_HOST = config_data['database']['host']
DB_PORT = config_data['database']['port']
DB_USER = config_data['database']['user']
DB_PASSWORD = config_data['database']['password']
DB_NAME = config_data['database']['name']

# 支付配置
CRYPTO_PAYMENT_ENABLED = config_data['payment']['crypto_enabled']
THIRD_PARTY_PAYMENT_ENABLED = config_data['payment']['third_party_enabled']
CARD_PAYMENT_ENABLED = config_data['payment']['card_enabled']

# 订阅配置
SUBSCRIPTION_PLANS = config_data['subscription']['plans']

# 通知配置
EMAIL_NOTIFICATIONS_ENABLED = config_data['email']['notifications_enabled']
EMAIL_SENDER = config_data['email']['sender']
SMTP_SERVER = config_data['email']['smtp']['server']
SMTP_PORT = config_data['email']['smtp']['port']
SMTP_USERNAME = config_data['email']['smtp']['username']
SMTP_PASSWORD = config_data['email']['smtp']['password']

# 消息配置
WELCOME_MESSAGE = config_data['messages']['welcome']
HELP_MESSAGE = config_data['messages']['help']

# 系统配置
LOG_LEVEL = config_data['system']['log_level']
TIMEZONE = config_data['system']['timezone']