#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识星球会员同步定时任务

每 10 分钟自动下载并同步会员数据
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

from zsxq_downloader import auto_download


def run_sync():
    """执行同步任务"""
    logger.info("=" * 50)
    logger.info(f"开始同步知识星球会员数据 {datetime.now()}")
    logger.info("=" * 50)

    try:
        result = auto_download()
        if result:
            logger.info(f"✅ 同步成功: {result}")
        else:
            logger.warning("⚠️ 同步未完成")
    except Exception as e:
        logger.error(f"❌ 同步失败: {e}")


def main():
    INTERVAL = int(os.getenv("ZSXQ_SYNC_INTERVAL", "10"))

    logger.info(f"知识星球会员同步服务启动，间隔 {INTERVAL} 分钟")
    logger.info("首次执行...")
    run_sync()

    schedule.every(INTERVAL).minutes.do(run_sync)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
