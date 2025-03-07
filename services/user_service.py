# 用户服务

import datetime
from database.models import User, Subscription
from database.db_manager import DatabaseManager

class UserService:
    """
    用户服务类，处理用户相关的业务逻辑
    """
    
    @staticmethod
    def register_user(telegram_id, username=None, first_name=None, last_name=None):
        """
        注册新用户或更新现有用户信息
        """
        try:
            user = User(telegram_id, username, first_name, last_name)
            user_id = user.save()
            return user_id
        except Exception as e:
            print(f"注册用户失败: {e}")
            return None
    
    @staticmethod
    def get_user(telegram_id):
        """
        获取用户信息
        """
        try:
            return DatabaseManager.get_user_by_telegram_id(telegram_id)
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None
    
    @staticmethod
    def update_user_email(telegram_id, email):
        """
        更新用户邮箱
        """
        try:
            user_data = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user_data:
                return False
                
            user = User(telegram_id, user_data['username'], user_data['first_name'], 
                       user_data['last_name'], email)
            user.save()
            return True
        except Exception as e:
            print(f"更新用户邮箱失败: {e}")
            return False
    
    @staticmethod
    def check_vip_status(telegram_id):
        """
        检查用户VIP状态
        """
        try:
            user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False, None
                
            return user['is_vip'], user['subscription_end_date']
        except Exception as e:
            print(f"检查VIP状态失败: {e}")
            return False, None
    
    @staticmethod
    def activate_vip_with_card(telegram_id, card_key):
        """
        使用卡密激活VIP
        """
        try:
            # 获取用户ID
            user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False, "用户不存在"
                
            # 使用卡密
            card = DatabaseManager.use_card_key(card_key, user['id'])
            if not card:
                return False, "卡密无效或已被使用"
                
            # 创建订阅
            from config import SUBSCRIPTION_PLANS
            plan_type = card['plan_type']
            
            if plan_type not in SUBSCRIPTION_PLANS:
                return False, "无效的订阅计划"
                
            plan = SUBSCRIPTION_PLANS[plan_type]
            start_date = datetime.datetime.now()
            end_date = start_date + datetime.timedelta(days=plan['duration_days'])
            
            subscription = Subscription(user['id'], plan_type, start_date, end_date)
            subscription_id = subscription.save()
            
            # 创建支付记录
            DatabaseManager.create_payment(
                user['id'], 
                'card', 
                plan['price'], 
                'CNY', 
                subscription_id,
                {'card_key_id': card['id']}
            )
            
            # 创建通知
            notification_title = "VIP激活成功"
            notification_content = f"您已成功激活{plan['name']}，有效期至{end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            
            DatabaseManager.create_notification(
                user['id'],
                'payment_success',
                notification_title,
                notification_content,
                is_email=True,
                is_telegram=True
            )
            
            return True, f"成功激活{plan['name']}，有效期至{end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            print(f"激活VIP失败: {e}")
            return False, f"激活失败: {str(e)}"
    
    @staticmethod
    def cancel_subscription(telegram_id):
        """
        取消用户订阅
        """
        try:
            # 获取用户ID
            user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False, "用户不存在"
                
            # 获取活跃订阅
            subscription = Subscription.get_active_by_user_id(user['id'])
            if not subscription:
                return False, "没有活跃的订阅"
                
            # 取消订阅
            result = Subscription.cancel_subscription(subscription['id'])
            if not result:
                return False, "取消订阅失败"
                
            # 创建通知
            notification_title = "订阅已取消"
            notification_content = "您的VIP订阅已成功取消"
            
            DatabaseManager.create_notification(
                user['id'],
                'system',
                notification_title,
                notification_content,
                is_email=True,
                is_telegram=True
            )
            
            return True, "订阅已成功取消"
            
        except Exception as e:
            print(f"取消订阅失败: {e}")
            return False, f"取消失败: {str(e)}"
    
    @staticmethod
    def get_subscription_info(telegram_id):
        """
        获取用户订阅信息
        """
        try:
            # 获取用户ID
            user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return None
                
            # 获取活跃订阅
            subscription = Subscription.get_active_by_user_id(user['id'])
            if not subscription:
                return None
                
            from config import SUBSCRIPTION_PLANS
            plan_type = subscription['plan_type']
            plan_info = SUBSCRIPTION_PLANS.get(plan_type, {})
            
            return {
                'subscription_id': subscription['id'],
                'plan_type': plan_type,
                'plan_name': plan_info.get('name', plan_type),
                'start_date': subscription['start_date'],
                'end_date': subscription['end_date'],
                'is_active': subscription['is_active'],
                'auto_renew': subscription['auto_renew']
            }
            
        except Exception as e:
            print(f"获取订阅信息失败: {e}")
            return None