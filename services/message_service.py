# 消息服务

from database.db_manager import DatabaseManager


class MessageService:
    """
    消息服务类，处理消息相关的业务逻辑
    """
    
    @staticmethod
    def create_message(title, content, is_vip_only=True, created_by=None, with_ad=False, ad_content=None):
        """
        创建消息
        
        参数:
            title: 消息标题
            content: 消息内容
            is_vip_only: 是否仅VIP用户可见
            created_by: 创建者ID
            with_ad: 是否包含广告
            ad_content: 广告内容
        
        返回:
            (success, message_id或错误信息)
        """
        try:
            # 如果包含广告，将广告内容添加到消息中
            if with_ad and ad_content:
                content = f"{content}\n\n---\n{ad_content}"
                
            # 创建消息
            message_id = DatabaseManager.create_message(title, content, is_vip_only, created_by)
            return True, message_id
        except Exception as e:
            print(f"创建消息失败: {e}")
            return False, f"创建消息失败: {str(e)}"
    
    @staticmethod
    def send_message_to_users(message_id, user_ids=None):
        """
        发送消息给用户
        如果user_ids为None，则根据消息的is_vip_only属性决定发送给所有用户还是仅VIP用户
        
        参数:
            message_id: 消息ID
            user_ids: 用户ID列表，为None时自动选择接收用户
            
        返回:
            (success, 发送数量或错误信息)
        """
        try:
            sent_count = DatabaseManager.send_message_to_users(message_id, user_ids)
            return True, sent_count
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False, f"发送消息失败: {str(e)}"
    
    @staticmethod
    def send_direct_message_to_vip(title, content, with_ad=False, ad_content=None, created_by=None):
        """
        直接向VIP用户发送专属消息
        
        参数:
            title: 消息标题
            content: 消息内容
            with_ad: 是否包含广告
            ad_content: 广告内容
            created_by: 创建者ID
            
        返回:
            (success, 发送数量或错误信息)
        """
        try:
            # 创建VIP专属消息
            success, message_id = MessageService.create_message(
                title, content, True, created_by, with_ad, ad_content
            )
            
            if not success:
                return False, message_id  # 返回错误信息
            
            # 发送给所有VIP用户
            return MessageService.send_message_to_users(message_id)
        except Exception as e:
            print(f"发送VIP专属消息失败: {e}")
            return False, f"发送VIP专属消息失败: {str(e)}"
    
    @staticmethod
    def send_channel_announcement(title, content, vip_only=True, with_ad=False, ad_content=None, created_by=None):
        """
        在频道中发送公告
        
        参数:
            title: 公告标题
            content: 公告内容
            vip_only: 是否仅对VIP用户可见
            with_ad: 是否包含广告
            ad_content: 广告内容
            created_by: 创建者ID
            
        返回:
            (success, 消息ID或错误信息)
        """
        try:
            # 创建频道公告
            success, message_id = MessageService.create_message(
                title, content, vip_only, created_by, with_ad, ad_content
            )
            
            if not success:
                return False, message_id  # 返回错误信息
                
            # 这里可以添加将消息发送到Telegram频道的逻辑
            # 需要集成Telegram Bot API
            
            return True, message_id
        except Exception as e:
            print(f"发送频道公告失败: {e}")
            return False, f"发送频道公告失败: {str(e)}"
    
    @staticmethod
    def get_user_messages(user_id, include_read=False, limit=20, offset=0):
        """
        获取用户的消息列表
        
        参数:
            user_id: 用户ID
            include_read: 是否包含已读消息
            limit: 返回消息数量限制
            offset: 分页偏移量
            
        返回:
            消息列表
        """
        try:
            query = """
            SELECT m.*, md.is_read, md.delivered_at, md.read_at 
            FROM messages m 
            JOIN message_deliveries md ON m.id = md.message_id 
            WHERE md.user_id = %s
            """
            
            params = [user_id]
            
            if not include_read:
                query += " AND md.is_read = FALSE"
                
            query += " ORDER BY m.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            return DatabaseManager.execute_query(query, params)
        except Exception as e:
            print(f"获取用户消息失败: {e}")
            return []
    
    @staticmethod
    def mark_message_as_read(message_id, user_id):
        """
        标记消息为已读
        
        参数:
            message_id: 消息ID
            user_id: 用户ID
            
        返回:
            是否成功
        """
        try:
            query = """
            UPDATE message_deliveries 
            SET is_read = TRUE, read_at = NOW() 
            WHERE message_id = %s AND user_id = %s
            """
            
            DatabaseManager.execute_query(query, (message_id, user_id))
            return True
        except Exception as e:
            print(f"标记消息已读失败: {e}")
            return False