# -*- coding: utf-8 -*-
"""
===================================
VIP 绑定命令
==================================

用户绑定知识星球昵称以开通 VIP。
"""

import logging
from typing import List, Optional

from bot.commands.base import BotCommand
from bot.models import BotMessage, BotResponse
from src.services.vip_service import is_vip, get_vip_info, get_vip_count

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
        return ["绑定", "vip", "会员"]

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
        if not args:
            return BotResponse(
                text=self._get_help_text(),
                success=True,
            )

        nickname = " ".join(args).strip()

        if not nickname:
            return BotResponse(
                text="请输入要绑定的昵称",
                success=False,
            )

        if is_vip(nickname):
            info = get_vip_info(nickname)
            extra_info = ""
            if info:
                for k, v in info.items():
                    if k.lower() != "nickname" and v:
                        extra_info += f"\n{k}: {v}"

            return BotResponse(
                text=f"✅ 验证成功！\n\n昵称: {nickname}\nVIP 状态: 已开通" + extra_info,
                success=True,
            )
        else:
            vip_count = get_vip_count()
            return BotResponse(
                text=f"❌ 验证失败\n\n未找到成员 [{nickname}]\n\n请检查：\n1. 昵称是否正确\n2. 是否已加入知识星球\n3. 是否刚加入（等待10分钟同步）\n\n当前VIP总数: {vip_count}",
                success=False,
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
