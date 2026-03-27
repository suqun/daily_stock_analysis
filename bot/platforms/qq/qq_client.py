# -*- coding: utf-8 -*-
"""
==================================
QQ (OpenClaw) 客户端
==================================

基于 OpenClaw HTTP API 的 QQ 机器人客户端。
支持发送消息到私聊/群聊，权限验证，限速控制。

API 文档：https://github.com/openclaw/openclaw
"""

import json
import logging
import time
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

from bot.models import BotMessage, BotResponse, ChatType
from src.formatters import chunk_content_by_max_bytes
from src.config import get_config

logger = logging.getLogger(__name__)

# 尝试导入 requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("[QQ] requests 库未安装，QQ 机器人不可用")


# ==================== 配置类 ====================

@dataclass
class QQBotConfig:
    """QQ 机器人配置"""
    # OpenClaw 连接
    openclaw_url: str = ""
    openclaw_token: str = ""
    
    # 管理员
    admin_qq: List[str] = field(default_factory=list)
    
    # 权限控制
    allow_groups: List[str] = field(default_factory=list)  # 空表示允许所有群
    enable_private_chat: bool = True
    
    # 限速控制
    msg_rate_limit: float = 1.0  # 秒/条
    daily_cmd_limit: int = 20  # 每日指令次数限制
    
    # 消息配置
    max_bytes: int = 5000  # 单条消息最大字节数
    
    @classmethod
    def from_config(cls, config) -> 'QQBotConfig':
        """从配置对象加载"""
        return cls(
            openclaw_url=getattr(config, 'qq_openclaw_url', '') or '',
            openclaw_token=getattr(config, 'qq_openclaw_token', '') or '',
            admin_qq=_parse_list(getattr(config, 'qq_admin_qq', '')),
            allow_groups=_parse_list(getattr(config, 'qq_allow_groups', '')),
            enable_private_chat=getattr(config, 'qq_enable_private_chat', True),
            msg_rate_limit=float(getattr(config, 'qq_msg_rate_limit', 1.0)),
            daily_cmd_limit=int(getattr(config, 'qq_daily_cmd_limit', 20)),
            max_bytes=int(getattr(config, 'qq_max_bytes', 5000)),
        )


def _parse_list(value: str) -> List[str]:
    """解析逗号分隔的字符串为列表"""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    return [v.strip() for v in str(value).split(',') if v.strip()]


# ==================== 限速器 ====================

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._last_send_time: Dict[str, float] = defaultdict(float)
    
    def can_send(self, key: str) -> bool:
        """检查是否可以发送"""
        now = time.time()
        if now - self._last_send_time[key] >= self.min_interval:
            self._last_send_time[key] = now
            return True
        return False
    
    def wait_if_needed(self, key: str) -> None:
        """如果需要则等待"""
        now = time.time()
        elapsed = now - self._last_send_time[key]
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_send_time[key] = time.time()


class DailyCmdLimiter:
    """每日指令次数限制器"""
    
    def __init__(self, daily_limit: int = 20):
        self.daily_limit = daily_limit
        self._cmd_count: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._last_reset: Dict[str, datetime] = defaultdict(datetime.now)
    
    def _reset_if_needed(self, user_id: str) -> None:
        """每日零点重置"""
        now = datetime.now()
        if (now - self._last_reset[user_id]).days >= 1:
            self._cmd_count[user_id] = defaultdict(int)
            self._last_reset[user_id] = now
    
    def can_execute(self, user_id: str) -> bool:
        """检查是否可以执行指令"""
        self._reset_if_needed(user_id)
        return self._cmd_count[user_id]['total'] < self.daily_limit
    
    def record(self, user_id: str) -> None:
        """记录一次指令执行"""
        self._reset_if_needed(user_id)
        self._cmd_count[user_id]['total'] += 1
    
    def get_remaining(self, user_id: str) -> int:
        """获取剩余次数"""
        self._reset_if_needed(user_id)
        return max(0, self.daily_limit - self._cmd_count[user_id]['total'])


# ==================== QQ 客户端 ====================

class QQReplyClient:
    """
    QQ 消息回复客户端
    
    通过 OpenClaw HTTP API 发送消息。
    """
    
    def __init__(self, config: QQBotConfig):
        """
        Args:
            config: QQ 机器人配置
        """
        self._config = config
        self._rate_limiter = RateLimiter(config.msg_rate_limit)
        self._cmd_limiter = DailyCmdLimiter(config.daily_cmd_limit)
        self._session = requests.Session()
        
        # 重试配置
        self._max_retries = 3
        self._retry_delay = 1.0
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
        }
        if self._config.openclaw_token:
            headers["Authorization"] = f"Bearer {self._config.openclaw_token}"
        return headers
    
    def _send_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retry: int = 0
    ) -> Optional[Dict]:
        """发送 HTTP 请求"""
        url = f"{self._config.openclaw_url.rstrip('/')}{endpoint}"
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                headers=self._build_headers(),
                timeout=30,
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 限流，等待后重试
                if retry < self._max_retries:
                    logger.warning(f"[QQ] 限流触发，等待后重试 ({retry + 1}/{self._max_retries})")
                    time.sleep(2 ** retry)
                    return self._send_request(method, endpoint, data, retry + 1)
                else:
                    logger.error(f"[QQ] 限流重试次数超限")
                    return None
            else:
                logger.error(f"[QQ] 请求失败: {response.status_code} {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            if retry < self._max_retries:
                logger.warning(f"[QQ] 请求异常，等待后重试 ({retry + 1}/{self._max_retries}): {e}")
                time.sleep(self._retry_delay * (retry + 1))
                return self._send_request(method, endpoint, data, retry + 1)
            logger.error(f"[QQ] 请求异常: {e}")
            return None
    
    def send_message(
        self,
        target: str,
        message: str,
        is_group: bool = False,
    ) -> bool:
        """
        发送消息到 QQ
        
        Args:
            target: 目标 ID (QQ号 或 群号)
            message: 消息内容
            is_group: 是否为群聊
            
        Returns:
            是否发送成功
        """
        if not self._config.openclaw_url:
            logger.warning("[QQ] OpenClaw URL 未配置")
            return False
        
        # 速率限制
        self._rate_limiter.wait_if_needed(target)
        
        # 格式化消息 (QQ 不支持 Markdown，简单处理)
        formatted_message = self._format_message(message)
        
        # 检查长度，分段发送
        content_bytes = len(formatted_message.encode('utf-8'))
        if content_bytes > self._config.max_bytes:
            logger.info(f"[QQ] 消息超长({content_bytes}字节)，分批发送")
            return self._send_chunked(target, formatted_message, is_group)
        
        return self._send_single(target, formatted_message, is_group)
    
    def _format_message(self, content: str) -> str:
        """格式化消息 (QQ 简单文本)"""
        # 移除 Markdown 格式符号
        lines = content.split('\n')
        result = []
        for line in lines:
            # 移除常见的 Markdown 符号
            line = line.replace('**', '').replace('*', '').replace('`', '')
            line = line.replace('#', '').replace('-', '').strip()
            if line:
                result.append(line)
        return '\n'.join(result)
    
    def _send_single(
        self,
        target: str,
        message: str,
        is_group: bool,
    ) -> bool:
        """发送单条消息"""
        channel = "group" if is_group else "private"
        
        payload = {
            "channel": "qq",
            "target": target,
            "message": message,
        }
        
        result = self._send_request("POST", "/api/message/send", payload)
        
        if result and result.get("status") == "sent":
            logger.info(f"[QQ] 消息发送成功 -> {channel}:{target}")
            return True
        
        logger.error(f"[QQ] 消息发送失败: {result}")
        return False
    
    def _send_chunked(
        self,
        target: str,
        message: str,
        is_group: bool,
    ) -> bool:
        """分批发送长消息"""
        chunks = chunk_content_by_max_bytes(
            message,
            self._config.max_bytes,
            add_page_marker=True
        )
        
        success_count = 0
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            if self._send_single(target, chunk, is_group):
                success_count += 1
            if i < total - 1:
                time.sleep(1)  # 批次间隔
        
        return success_count == total
    
    def reply_to_message(
        self,
        user_id: str,
        message: str,
        is_group: bool = False,
    ) -> bool:
        """
        回复消息
        
        Args:
            user_id: 用户 QQ 号
            message: 回复内容
            is_group: 是否在群聊中
            
        Returns:
            是否发送成功
        """
        return self.send_message(user_id, message, is_group)
    
    # ==================== 权限检查 ====================
    
    def is_admin(self, user_id: str) -> bool:
        """检查是否为管理员"""
        return user_id in self._config.admin_qq
    
    def is_group_allowed(self, group_id: str) -> bool:
        """检查群是否在白名单"""
        if not self._config.allow_groups:
            return True  # 空列表表示允许所有
        return group_id in self._config.allow_groups
    
    def can_send_to_user(self, user_id: str) -> bool:
        """检查是否可以发送消息给用户"""
        # 管理员始终可以
        if self.is_admin(user_id):
            return True
        # 检查私聊开关
        if not self._config.enable_private_chat:
            return False
        # 检查指令次数限制
        return self._cmd_limiter.can_execute(user_id)
    
    def record_cmd_usage(self, user_id: str) -> bool:
        """
        记录指令使用
        
        Returns:
            是否允许执行 (未超限)
        """
        if self.is_admin(user_id):
            return True
        if self._cmd_limiter.can_execute(user_id):
            self._cmd_limiter.record(user_id)
            return True
        return False
    
    def get_cmd_remaining(self, user_id: str) -> int:
        """获取剩余指令次数"""
        return self._cmd_limiter.get_remaining(user_id)


# ==================== Webhook 处理器 ====================

class QQWebhookHandler:
    """
    QQ Webhook 事件处理器
    
    解析 OpenClaw 发送的 Webhook 事件，
    转换为统一的 BotMessage 格式。
    """
    
    def __init__(self, reply_client: QQReplyClient):
        """
        Args:
            reply_client: QQ 回复客户端
        """
        self._reply_client = reply_client
    
    def parse_event(self, data: Dict[str, Any]) -> Optional[BotMessage]:
        """
        解析 Webhook 事件为 BotMessage
        
        Args:
            data: Webhook 请求数据
            
        Returns:
            BotMessage 对象，或 None (不需要处理)
        """
        try:
            # OpenClaw Webhook 格式
            # {
            #   "channel": "qq",
            #   "event": "message",
            #   "message": "...",
            #   "from": "123456",
            #   "group": "987654",  // 群号，私聊时无
            #   "message_id": "xxx",
            #   "timestamp": "..."
            # }
            
            channel = data.get("channel")
            if channel != "qq":
                logger.debug(f"[QQ] 忽略非 QQ 频道事件: {channel}")
                return None
            
            event_type = data.get("event", data.get("type"))
            
            # 只处理消息事件
            if event_type not in ("message", "private_message", "group_message"):
                logger.debug(f"[QQ] 忽略非消息事件: {event_type}")
                return None
            
            # 提取消息内容
            message_content = data.get("message", "") or data.get("content", "") or ""
            if not message_content:
                return None
            
            # 提取发送者信息
            user_id = str(data.get("from", data.get("user_id", "")))
            if not user_id:
                return None
            
            # 提取群信息
            group_id = str(data.get("group", data.get("group_id", "")))
            
            # 确定聊天类型
            if group_id:
                chat_type = ChatType.GROUP
                chat_id = group_id
            else:
                chat_type = ChatType.PRIVATE
                chat_id = user_id
            
            # 权限检查 (群白名单)
            if chat_type == ChatType.GROUP:
                if not self._reply_client.is_group_allowed(group_id):
                    logger.info(f"[QQ] 忽略未授权群: {group_id}")
                    return None
            
            # 提取消息 ID
            message_id = data.get("message_id", "") or data.get("mid", "")
            
            # 解析命令 (去除 @机器人 等)
            content = self._extract_command(message_content)
            
            # 检查是否为命令
            is_command = content.startswith('/') or content.startswith('!')
            
            # 创建消息对象
            return BotMessage(
                platform="qq",
                message_id=message_id,
                user_id=user_id,
                user_name=user_id,  # QQ 不返回昵称
                chat_id=chat_id,
                chat_type=chat_type,
                content=content,
                raw_content=message_content,
                mentioned=False,
                mentions=[],
                timestamp=datetime.now(),
                raw_data=data,
            )
            
        except Exception as e:
            logger.error(f"[QQ] 解析事件失败: {e}")
            return None
    
    def _extract_command(self, text: str) -> str:
        """提取命令内容"""
        text = text.strip()
        # 移除空白
        return ' '.join(text.split())
    
    def handle_event(
        self,
        data: Dict[str, Any],
        on_message,
    ) -> Optional[BotResponse]:
        """
        处理 Webhook 事件
        
        Args:
            data: Webhook 请求数据
            on_message: 消息处理回调函数
            
        Returns:
            BotResponse 响应消息
        """
        # 解析消息
        message = self.parse_event(data)
        if message is None:
            return None
        
        # 权限检查 - 私聊需要检查是否可发送
        if message.chat_type == ChatType.PRIVATE:
            if not self._reply_client.can_send_to_user(message.user_id):
                logger.info(f"[QQ] 用户 {message.user_id} 指令次数超限")
                return BotResponse(
                    text="抱歉，您今日的指令次数已用完，请明天再来~",
                    at_user=False,
                )
        
        # 记录指令使用
        self._reply_client.record_cmd_usage(message.user_id)
        
        # 调用消息处理回调
        response = on_message(message)
        
        # 发送回复
        if response and response.text:
            self._reply_client.send_message(
                target=message.chat_id,
                message=response.text,
                is_group=(message.chat_type == ChatType.GROUP),
            )
        
        return response


# ==================== 客户端工厂 ====================

_qq_client: Optional[QQReplyClient] = None
_qq_handler: Optional[QQWebhookHandler] = None


def get_qq_client() -> Optional[QQReplyClient]:
    """获取全局 QQ 客户端实例"""
    global _qq_client
    
    if _qq_client is None:
        if not REQUESTS_AVAILABLE:
            logger.warning("[QQ] requests 库未安装")
            return None
        
        try:
            config = get_config()
            qq_config = QQBotConfig.from_config(config)
            
            if not qq_config.openclaw_url:
                logger.info("[QQ] OpenClaw URL 未配置，跳过初始化")
                return None
            
            _qq_client = QQReplyClient(qq_config)
            _qq_handler = QQWebhookHandler(_qq_client)
            
            logger.info(f"[QQ] 客户端初始化成功: {qq_config.openclaw_url}")
            
        except Exception as e:
            logger.error(f"[QQ] 客户端初始化失败: {e}")
            return None
    
    return _qq_client


def get_qq_handler() -> Optional[QQWebhookHandler]:
    """获取全局 QQ Webhook 处理器"""
    global _qq_handler
    
    if _qq_handler is None:
        client = get_qq_client()
        if client:
            _qq_handler = QQWebhookHandler(client)
    
    return _qq_handler


def handle_qq_webhook(data: Dict[str, Any]) -> Optional[BotResponse]:
    """
    处理 QQ Webhook 事件的便捷函数
    
    Args:
        data: Webhook 请求数据
        
    Returns:
        BotResponse 响应消息
    """
    handler = get_qq_handler()
    if handler is None:
        logger.warning("[QQ] Webhook 处理器未初始化")
        return None
    
    # 导入 dispatcher
    from bot.dispatcher import get_dispatcher
    
    def on_message(msg: BotMessage) -> BotResponse:
        dispatcher = get_dispatcher()
        return dispatcher.dispatch(msg)
    
    return handler.handle_event(data, on_message)


# ==================== 可用性标志 ====================

QQ_AVAILABLE = REQUESTS_AVAILABLE
