# -*- coding: utf-8 -*-
"""
===================================
可用策略列表命令
==================================

显示系统中可用的分析策略列表。
"""

import os
import logging
from typing import List, Optional

from bot.commands.base import BotCommand
from bot.models import BotMessage, BotResponse

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ListCommand(BotCommand):
    """
    可用策略列表命令
    
    显示系统中可用的分析策略。
    
    用法：
        /list         - 显示所有可用策略
    """
    
    @property
    def name(self) -> str:
        return "list"
    
    @property
    def aliases(self) -> List[str]:
        return ["l", "strategies", "列表", "策略"]
    
    @property
    def description(self) -> str:
        return "显示可用策略列表"
    
    @property
    def usage(self) -> str:
        return "/list"
    
    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        """执行策略列表命令"""
        strategies = self._load_strategies()
        
        if not strategies:
            return BotResponse.text_response("暂无可用策略")
        
        lines = ["📋 **可用策略列表**\n"]
        
        for name, info in strategies.items():
            display_name = info.get("display_name", name)
            desc = info.get("description", "")
            lines.append(f"• **{display_name}** (`{name}`)")
            if desc:
                lines.append(f"  {desc}")
        
        lines.append("\n使用 `/analyze <股票代码> -skill <策略名>` 来使用特定策略")
        
        return BotResponse.markdown_response("\n".join(lines))
    
    def _load_strategies(self) -> dict:
        """加载策略列表"""
        strategies = {}
        strategies_dir = os.path.join(BASE_DIR, "strategies")
        
        if not os.path.exists(strategies_dir):
            return strategies
        
        import yaml
        
        for filename in os.listdir(strategies_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(strategies_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)
                        if config and isinstance(config, dict):
                            name = config.get("name", filename[:-5])
                            strategies[name] = {
                                "display_name": config.get("display_name", name),
                                "description": config.get("description", "")[:50],
                            }
                except Exception as e:
                    logger.warning(f"加载策略文件失败 {filename}: {e}")
        
        return strategies
