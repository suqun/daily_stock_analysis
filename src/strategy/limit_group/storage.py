# -*- coding: utf-8 -*-
# Model is in src.storage (LimitGroupStock), imported via src.storage for backward compat.
# Functions are decoupled here following OCP.
from src.storage import LimitGroupStock

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, desc, select

from src.storage import get_db

logger = __import__('logging').getLogger(__name__)


def _stock_to_dict(stock: LimitGroupStock) -> Dict[str, Any]:
    return {
        "stock_code": stock.stock_code,
        "stock_name": stock.stock_name,
        "group_name": stock.group_name,
        "insert_time": stock.insert_time,
        "observe_days": stock.observe_days,
        "is_selected": stock.is_selected,
        "selected_time": stock.selected_time,
        "selected_reason": stock.selected_reason,
        "status": stock.status,
        "last_check_time": stock.last_check_time,
    }


def add_limit_group_stock(stock_code: str, stock_name: str, group_name: str) -> Dict[str, Any]:
    if not stock_code or not group_name:
        raise ValueError("股票代码和分组名称不能为空")
    db = get_db()
    now = datetime.now()
    with db.session_scope() as session:
        existing = session.execute(
            select(LimitGroupStock).where(
                and_(
                    LimitGroupStock.stock_code == stock_code,
                    LimitGroupStock.group_name == group_name,
                    LimitGroupStock.status == 'active'
                )
            )
        ).scalar_one_or_none()
        if existing:
            logger.debug(f"股票 {stock_code} 已在分组 {group_name} 中，跳过添加")
            return _stock_to_dict(existing)
        record = LimitGroupStock(
            stock_code=stock_code,
            stock_name=stock_name,
            group_name=group_name,
            insert_time=now,
            observe_days=0,
            is_selected=False,
            status='active',
            last_check_time=now,
        )
        session.add(record)
        session.flush()
        logger.info(f"添加 {stock_code}({stock_name}) 到分组 {group_name}，插入时间: {now}")
        return _stock_to_dict(record)


def get_limit_group_stocks_by_group(group_name: str) -> List[Dict[str, Any]]:
    if not group_name:
        return []
    db = get_db()
    with db.session_scope() as session:
        results = session.execute(
            select(LimitGroupStock)
            .where(and_(
                LimitGroupStock.group_name == group_name,
                LimitGroupStock.status == 'active'
            ))
            .order_by(desc(LimitGroupStock.insert_time))
        ).scalars().all()
        return [_stock_to_dict(r) for r in results]


def get_all_active_limit_group_stocks() -> List[Dict[str, Any]]:
    db = get_db()
    with db.session_scope() as session:
        results = session.execute(
            select(LimitGroupStock)
            .where(LimitGroupStock.status == 'active')
            .order_by(LimitGroupStock.insert_time)
        ).scalars().all()
        return [_stock_to_dict(r) for r in results]


def get_selected_stocks_with_details() -> List[Dict[str, Any]]:
    db = get_db()
    with db.session_scope() as session:
        results = session.execute(
            select(LimitGroupStock)
            .where(and_(
                LimitGroupStock.is_selected == True,
                LimitGroupStock.status == 'active'
            ))
            .order_by(desc(LimitGroupStock.selected_time))
        ).scalars().all()
        return [_stock_to_dict(r) for r in results]


def update_limit_group_stock_observe_days(stock_code: str, group_name: str, observe_days: int) -> bool:
    db = get_db()
    with db.session_scope() as session:
        record = session.execute(
            select(LimitGroupStock).where(
                and_(
                    LimitGroupStock.stock_code == stock_code,
                    LimitGroupStock.group_name == group_name,
                    LimitGroupStock.status == 'active'
                )
            )
        ).scalar_one_or_none()
        if not record:
            logger.warning(f"未找到股票 {stock_code} 在分组 {group_name} 中的记录")
            return False
        record.observe_days = observe_days
        record.last_check_time = datetime.now()
        session.flush()
        logger.debug(f"更新 {stock_code} 在 {group_name} 的观察天数为 {observe_days}")
        return True


def mark_stock_as_selected(stock_code: str, group_name: str, selected_reason: str) -> bool:
    db = get_db()
    now = datetime.now()
    with db.session_scope() as session:
        record = session.execute(
            select(LimitGroupStock).where(
                and_(
                    LimitGroupStock.stock_code == stock_code,
                    LimitGroupStock.group_name == group_name,
                    LimitGroupStock.status == 'active'
                )
            )
        ).scalar_one_or_none()
        if not record:
            logger.warning(f"未找到股票 {stock_code} 在分组 {group_name} 中的记录")
            return False
        record.is_selected = True
        record.selected_time = now
        record.selected_reason = selected_reason
        session.flush()
        logger.info(f"标记 {stock_code} 为精选自选，理由: {selected_reason}")
        return True


def remove_stock_from_limit_group(stock_code: str, group_name: str) -> bool:
    db = get_db()
    with db.session_scope() as session:
        record = session.execute(
            select(LimitGroupStock).where(
                and_(
                    LimitGroupStock.stock_code == stock_code,
                    LimitGroupStock.group_name == group_name,
                    LimitGroupStock.status == 'active'
                )
            )
        ).scalar_one_or_none()
        if not record:
            logger.warning(f"未找到股票 {stock_code} 在分组 {group_name} 中的记录")
            return False
        record.status = 'removed'
        session.flush()
        logger.info(f"从分组 {group_name} 移除股票 {stock_code}")
        return True


def calculate_observe_days(stock_code: str, group_name: str) -> int:
    db = get_db()
    with db.session_scope() as session:
        record = session.execute(
            select(LimitGroupStock).where(
                and_(
                    LimitGroupStock.stock_code == stock_code,
                    LimitGroupStock.group_name == group_name,
                    LimitGroupStock.status == 'active'
                )
            )
        ).scalar_one_or_none()
        if not record or not record.insert_time:
            return 0
        delta = datetime.now() - record.insert_time
        return delta.days



def trigger_limit_up_strategy() -> bool:
    try:
        from .limit_up_track import daily_limit_up_strategy_check
        daily_limit_up_strategy_check()
        return True
    except ImportError as e:
        logger.error(f"涨停策略模块导入失败：{e}")
        return False
