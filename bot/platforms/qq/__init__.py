# -*- coding: utf-8 -*-
"""
===================================
QQ (OpenClaw) 机器人平台适配器
==================================

基于 OpenClaw (小龙虾) 官方 HTTP API 的 QQ 机器人接入。

功能：
- 消息发送（私聊/群聊）
- Webhook 事件接收
- 权限管理
- 限速控制

依赖：
- requests

配置项：
- QQ_OPENCLAW_URL: OpenClaw 服务地址 (如 http://127.0.0.1:18789)
- QQ_OPENCLAW_TOKEN: OpenClaw API Token
- QQ_ADMIN_QQ: 管理员 QQ 号
- QQ_ALLOW_GROUPS: 允许的群号列表
- QQ_ENABLE_PRIVATE_CHAT: 是否启用私聊
- QQ_MSG_RATE_LIMIT: 消息发送速率限制 (秒/条)

文档：
- OpenClaw: https://github.com/openclaw/openclaw
- QQ 机器人: https://q.qq.com/qqbot/openclaw/index.html
"""

from bot.platforms.qq.qq_client import (
    QQReplyClient,
    QQWebhookHandler,
    get_qq_client,
    get_qq_handler,
    handle_qq_webhook,
    QQ_AVAILABLE,
)

__all__ = [
    'QQReplyClient',
    'QQWebhookHandler',
    'get_qq_client',
    'get_qq_handler',
    'handle_qq_webhook',
    'QQ_AVAILABLE',
]
