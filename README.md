# Telegram VIP 付费机器人

这是一个基于Python和python-telegram-bot库开发的Telegram VIP付费机器人，提供用户管理、支付功能、消息管理和通知系统等功能。

## 功能特性

### 用户管理
- 保存用户付费状态（VIP/非VIP）
- 记录VIP订阅时长（按月、按年订阅）
- 自动续订、订阅到期处理
- 用户取消订阅功能
- 支持支付失败后的处理逻辑

### 支付功能
- 卡密支付：实现卡密形式的充值和VIP激活
- 数字货币支付：整合Telegram内置@wallet机器人，支持比特币、USDT、TON等数字货币支付
- 常规支付：如支付宝、微信支付、Stripe、PayPal等第三方支付集成

### 消息管理
- 机器人向VIP用户直接发送专属消息
- 在频道（Channel）中发送公告，确保只针对VIP用户
- 支持在消息中带上广告（可选）

### 通知功能
- 邮件通知用户（如支付成功、订阅到期提醒等）
- 支付失败、取消订阅的通知
- 系统消息推送（站内信、Telegram消息等）

## 技术栈
- Python
- python-telegram-bot
- MySQL
- 支付API集成

## 项目结构
```
├── config/                 # 配置文件目录
│   ├── config.py           # 主配置文件
│   └── secrets.py          # 密钥配置（不提交到版本控制）
├── database/               # 数据库相关
│   ├── models.py           # 数据模型定义
│   └── db_manager.py       # 数据库管理器
├── handlers/               # 消息处理器
│   ├── command_handlers.py # 命令处理
│   ├── payment_handlers.py # 支付相关处理
│   └── message_handlers.py # 消息处理
├── payments/               # 支付模块
│   ├── card_payment.py     # 卡密支付
│   ├── crypto_payment.py   # 加密货币支付
│   └── third_party.py      # 第三方支付
├── services/               # 业务逻辑
│   ├── user_service.py     # 用户服务
│   ├── subscription.py     # 订阅管理
│   └── notification.py     # 通知服务
├── utils/                  # 工具函数
│   ├── helpers.py          # 辅助函数
│   └── validators.py       # 验证函数
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包列表
└── README.md               # 项目说明
```

## 安装与配置

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 配置数据库和Telegram Bot Token
4. 运行：`python main.py`

## 使用说明

待补充

## 许可证

MIT