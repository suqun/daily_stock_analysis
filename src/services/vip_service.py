import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, date

from sqlalchemy import and_

from src.storage import DatabaseManager
from src.models.zsxq_member import ZsxqMember, Base

logger = logging.getLogger(__name__)

_db = None


def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
        Base.metadata.create_all(_db._engine)
    return _db


def parse_date(date_str) -> Optional[date]:
    """解析日期字符串"""
    if not date_str or str(date_str) == "nan":
        return None
    try:
        if isinstance(date_str, date):
            return date_str
        for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"]:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except:
                continue
        return None
    except:
        return None


def parse_datetime(dt_str) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not dt_str or str(dt_str) == "nan":
        return None
    try:
        if isinstance(dt_str, datetime):
            return dt_str
        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
            try:
                return datetime.strptime(str(dt_str), fmt)
            except:
                continue
        return None
    except:
        return None


def parse_float(val) -> Optional[float]:
    """解析浮点数"""
    if val is None or str(val) == "nan":
        return None
    try:
        return float(str(val).replace(",", ""))
    except:
        return None


def parse_int(val) -> Optional[int]:
    """解析整数"""
    if val is None or str(val) == "nan":
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except:
        return None


def sync_members_from_excel(excel_path: str) -> int:
    """从 Excel 同步会员数据到数据库"""
    import pandas as pd

    if not os.path.exists(excel_path):
        logger.warning(f"Excel 文件不存在: {excel_path}")
        return 0

    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        logger.error(f"读取 Excel 失败: {e}")
        return 0

    col_map = {
        "成员编号": "member_no",
        "用户加密id": "user_id",
        "用户昵称": "nickname",
        "微信昵称": "wechat_nickname",
        "星球名片昵称": "card_nickname",
        "星球内备注昵称": "remark_nickname",
        "知识号": "zhishihao",
        "手机号码": "phone",
        "微信号": "wechat",
        "身份": "identity",
        "是否付费加入": "is_paid",
        "首次加入时间": "join_date",
        "首次来源": "source",
        "到期时间": "expire_date",
        "距离可续期的天数": "days_to_renew",
        "已续期次数": "renew_count",
        "最后活跃时间": "last_active_time",
        "在本星球成功付费的总金额": "total_paid",
        "是否被拉黑": "is_blocked",
        "用户是否退出星球": "is_quit",
        "是否关注知识星球公众号": "is_followed",
        "是否开启消息通知": "notify_enabled",
        "粉丝数": "fans_count",
        "主题数": "topics_count",
        "评论数": "comments_count",
        "提问数": "questions_count",
        "提问金额": "question_amount",
        "回答数": "answers_count",
        "回答收入": "answer_income",
        "点赞数": "likes_given",
        "获赞数": "likes_received",
        "赞赏金额": "reward_given",
        "获得赞赏金额": "reward_received",
        "普通分享带来的用户数": "share_users",
        "普通分享带来的金额": "share_amount",
        "分享有赏带来的用户数": "share_reward_users",
        "分享有赏带来的订单数": "share_reward_orders",
        "分享有赏带来的金额": "share_reward_amount",
    }

    db = get_db()
    count = 0

    with db.session_scope() as session:
        for _, row in df.iterrows():
            nickname = str(row.get("用户昵称", "")).strip()
            if not nickname or nickname == "nan":
                continue

            exist = session.query(ZsxqMember).filter(
                ZsxqMember.nickname == nickname
            ).first()

            member_data = {"updated_at": datetime.now()}

            for cn_col, model_col in col_map.items():
                if cn_col not in row:
                    continue
                val = row.get(cn_col)
                if str(val) == "nan":
                    continue

                if model_col in ["join_date", "expire_date"]:
                    member_data[model_col] = parse_date(val)
                elif model_col in ["last_active_time"]:
                    member_data[model_col] = parse_datetime(val)
                elif model_col in ["is_paid", "is_blocked", "is_quit", "is_followed", "notify_enabled"]:
                    member_data[model_col] = str(val) in ["是", "True", "true", "1"]
                elif model_col in ["member_no", "days_to_renew", "renew_count", "fans_count", "topics_count", 
                                   "comments_count", "questions_count", "answers_count", "likes_given", 
                                   "likes_received", "share_users", "share_reward_users", "share_reward_orders"]:
                    member_data[model_col] = parse_int(val)
                elif model_col in ["total_paid", "question_amount", "answer_income", "reward_given", 
                                   "reward_received", "share_amount", "share_reward_amount"]:
                    member_data[model_col] = parse_float(val)
                else:
                    member_data[model_col] = str(val)

            if exist:
                for k, v in member_data.items():
                    if v is not None:
                        setattr(exist, k, v)
            else:
                member_data["nickname"] = nickname
                member_data["status"] = True
                member_data["created_at"] = datetime.now()
                member = ZsxqMember(**member_data)
                session.add(member)
                count += 1

    logger.info(f"同步会员数据完成，新增: {count}")
    return count


def is_vip(nickname: str) -> bool:
    """检查用户是否为 VIP"""
    if not nickname:
        return False

    db = get_db()
    with db.session_scope() as session:
        member = session.query(ZsxqMember).filter(
            and_(
                ZsxqMember.nickname == nickname.strip(),
                ZsxqMember.status == True
            )
        ).first()
        return member is not None


def get_vip_info(nickname: str) -> Optional[Dict]:
    """获取会员详细信息"""
    if not nickname:
        return None

    db = get_db()
    with db.session_scope() as session:
        member = session.query(ZsxqMember).filter(
            ZsxqMember.nickname == nickname.strip()
        ).first()

        if not member:
            return None

        return {
            "nickname": member.nickname,
            "user_id": member.user_id,
            "identity": member.identity,
            "is_paid": "是" if member.is_paid else "否",
            "join_date": str(member.join_date) if member.join_date else None,
            "expire_date": str(member.expire_date) if member.expire_date else None,
            "total_paid": member.total_paid,
            "is_blocked": "是" if member.is_blocked else "否",
            "is_quit": "是" if member.is_quit else "否",
            "status": "有效" if member.status else "无效",
        }


def get_vip_list() -> List[str]:
    """获取所有有效会员昵称列表"""
    db = get_db()
    with db.session_scope() as session:
        members = session.query(ZsxqMember.nickname).filter(
            ZsxqMember.status == True
        ).all()
        return [m[0] for m in members]


def get_vip_count() -> int:
    """获取有效会员总数"""
    db = get_db()
    with db.session_scope() as session:
        return session.query(ZsxqMember).filter(
            ZsxqMember.status == True
        ).count()


def add_vip(nickname: str, **kwargs) -> bool:
    """手动添加 VIP"""
    db = get_db()
    with db.session_scope() as session:
        exist = session.query(ZsxqMember).filter(
            ZsxqMember.nickname == nickname
        ).first()

        if exist:
            exist.status = True
            exist.updated_at = datetime.now()
            for k, v in kwargs.items():
                if hasattr(exist, k):
                    setattr(exist, k, v)
        else:
            member = ZsxqMember(nickname=nickname, status=True, **kwargs)
            session.add(member)
    return True


def remove_vip(nickname: str) -> bool:
    """移除 VIP"""
    db = get_db()
    with db.session_scope() as session:
        member = session.query(ZsxqMember).filter(
            ZsxqMember.nickname == nickname
        ).first()
        if member:
            member.status = False
            member.updated_at = datetime.now()
            return True
    return False


if __name__ == "__main__":
    print(f"VIP 总数: {get_vip_count()}")
    print(f"VIP 列表: {get_vip_list()[:10]}")
