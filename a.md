## 文本消息相关
- **`reply_text(text, **kwargs)`**：发送文本消息。
- **`edit_text(text, **kwargs)`**：编辑已有消息的文本（通常用于 inline 按钮后的消息编辑）。
- **`delete_message()`**：删除一条消息。

## 媒体消息相关
- **`reply_photo(photo, **kwargs)`**：发送图片。
- **`reply_video(video, **kwargs)`**：发送视频。
- **`reply_audio(audio, **kwargs)`**：发送音频。
- **`reply_voice(voice, **kwargs)`**：发送语音（像 Telegram 里的语音消息）。
- **`reply_document(document, **kwargs)`**：发送文件（如 PDF、Word 等）。
- **`reply_animation(animation, **kwargs)`**：发送 GIF 动图。
- **`reply_sticker(sticker, **kwargs)`**：发送贴纸。
- **`reply_video_note(video_note, **kwargs)`**：发送视频笔记（圆形视频）。

## 通知与状态相关
- **`send_chat_action(action)`**：发送"正在输入…"、"发送照片…"等状态（对用户是个友好的反馈）。
    - **`ChatAction.TYPING`**：正在输入。
    - **`ChatAction.UPLOAD_PHOTO`**：正在上传照片。
    - **`ChatAction.RECORD_AUDIO`**：正在录音。

## 按钮与交互
- **`reply_markup=InlineKeyboardMarkup(...)`**：发送 inline 按钮（按钮在消息里）。
- **`reply_markup=ReplyKeyboardMarkup(...)`**：发送自定义键盘（直接替换用户输入区）。
- **`reply_markup=ReplyKeyboardRemove()`**：移除自定义键盘。
- **`reply_markup=ForceReply()`**：强制用户回复某条消息。

## 转发与分享
- **`forward(chat_id, from_chat_id, message_id)`**：把一条消息转发到另一个聊天。
- **`copy_message(chat_id, from_chat_id, message_id)`**：把消息复制过去，不带原作者标签。

## 其他消息类型
- **`reply_location(latitude, longitude, **kwargs)`**：发送位置。
- **`reply_venue(latitude, longitude, title, address, **kwargs)`**：发送带名称和地址的位置（如商店、餐馆）。
- **`reply_contact(phone_number, first_name, **kwargs)`**：发送联系人信息。
- **`reply_poll(question, options, **kwargs)`**：创建投票。
- **`reply_dice(**kwargs)`**：发送一个随机骰子（🎲、🎯、🏀、⚽等）。