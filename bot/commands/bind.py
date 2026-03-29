# -*- coding: utf-8 -*-
"""
==================================
VIP 绑定命令
==================================

用户绑定知识星球昵称以开通 VIP。
"""

import logging
from typing import List, Optional

from bot.commands.base import BotCommand
from bot.models import BotMessage, BotResponse
from src.services.vip_service import (
    bind_qq, is_vip as check_is_vip, 
    get_bind_info, get_vip_count, get_free_usage
)

logger = logging.getLogger(__name__)


class BindCommand(BotCommand):
    """
    VIP 绑定命令

    用户绑定知识星球昵称，系统自动校验是否为星球成员。

    用法：
        /bind 昵称     - 绑定知识星球昵称
        /bind         - 查看绑定帮助
    """

    @property
    def name(self) -> str:
        return "bind"

    @property
    def aliases(self) -> List[str]:
        return ["绑定"]

    @property
    def description(self) -> str:
        return "绑定知识星球昵称开通VIP"

    @property
    def usage(self) -> str:
        return "/bind <星球昵称>"

    def validate_args(self, args: List[str]) -> Optional[str]:
        if not args:
            return None
        return None

    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        qq = message.user_id

        if not args:
            return BotResponse(
                text=self._get_help_text(),
            )

        nickname = " ".join(args).strip()

        if not nickname:
            return BotResponse(
                text="请输入要绑定的昵称",
            )

        ok, msg = bind_qq(qq, nickname)
        return BotResponse(
            text=msg,
        )

    def _get_help_text(self) -> str:
        return """📖 VIP 绑定说明

用法: /bind <星球昵称>

示例:
  /bind 张三
  /bind 我的昵称

说明:
1. 先加入知识星球
2. 10分钟后系统自动同步成员数据
3. 使用 /bind 你的昵称 绑定

如有疑问请联系管理员"""


class VipStatusCommand(BotCommand):
    """查询 VIP 状态"""

    @property
    def name(self) -> str:
        return "vip"

    @property
    def aliases(self) -> List[str]:
        return ["会员", "vip状态"]

    @property
    def description(self) -> str:
        return "查询VIP会员状态"

    @property
    def usage(self) -> str:
        return "/vip"

    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        qq = message.user_id

        bind_info = get_bind_info(qq)
        if not bind_info:
            return BotResponse(
                text="⚠️ 此为会员专属功能\n知识星球搜索：356745\n加入后发送 /bind 星球昵称 即可开通",
            )

        is_vip = check_is_vip(qq)
        if not is_vip:
            return BotResponse(
                text="⚠️ 你的VIP已过期\n\n请续费后重新绑定",
            )

        return BotResponse(
            text=f"""✅ VIP会员正常
星球昵称：{bind_info['nickname']}
绑定时间：{bind_info['bind_time']}
全部功能已解锁""",
        )
