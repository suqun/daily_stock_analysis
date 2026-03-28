import os
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date

from sqlalchemy import and_

from src.storage import DatabaseManager
from src.models.zsxq_member import ZsxqMember, Base as ZsxqBase
from src.models.vip_user import QqBind, FreeUsage, Base as VipBase

logger = logging.getLogger(__name__)

FREE_DAILY_LIMIT = 5

_db = None


def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
        ZsxqBase.metadata.create_all(_db._engine)
        VipBase.metadata.create_all(_db._engine)
    return _db


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
    }

    db = get_db()
    count = 0

    with db.session_scope() as session:
        for _, row in df.iterrows():
            nickname = str(row.get("用户昵称", "")).strip()
            if not nickname or nickname == "nan":
                continue

            expire_str = str(row.get("到期时间", ""))
            expire_date = None
            try:
                if expire_str and expire_str != "nan":
                    expire_date = datetime.strptime(expire_str, "%Y/%m/%d").date()
            except:
                pass

            is_paid = str(row.get("是否付费加入", "否")) == "是"

            exist = session.query(ZsxqMember).filter(
                ZsxqMember.nickname == nickname
            ).first()

            if exist:
                exist.expire_date = expire_date
                exist.is_paid = is_paid
                exist.updated_at = datetime.now()
            else:
                member = ZsxqMember(
                    nickname=nickname,
                    is_paid=is_paid,
                    expire_date=expire_date,
                    status=True,
                    identity="成员",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                session.add(member)
                count += 1

    logger.info(f"同步会员数据完成，新增: {count}")
    return count


def is_member(nickname: str) -> bool:
    """检查用户是否为星球会员"""
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


def is_vip_by_nickname(nickname: str) -> bool:
    """通过昵称检查是否为有效VIP（未过期）"""
    if not nickname:
        return False

    db = get_db()
    with db.session_scope() as session:
        member = session.query(ZsxqMember).filter(
            ZsxqMember.nickname == nickname.strip()
        ).first()

        if not member:
            return False

        if member.expire_date:
            today = date.today()
            if member.expire_date < today:
                return False

        return True


def get_member_info(nickname: str) -> Optional[Dict]:
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
            "identity": member.identity,
            "is_paid": "是" if member.is_paid else "否",
            "join_date": str(member.join_date) if member.join_date else None,
            "expire_date": str(member.expire_date) if member.expire_date else None,
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


def bind_qq(qq: str, nickname: str) -> Tuple[bool, str]:
    """绑定 QQ 号和星球昵称"""
    if not qq or not nickname:
        return False, "QQ号或昵称不能为空"

    if not is_member(nickname):
        return False, f"未找到星球会员 [{nickname}]\n请检查昵称是否正确"

    db = get_db()
    with db.session_scope() as session:
        exist = session.query(QqBind).filter(
            QqBind.qq == qq
        ).first()

        if exist:
            exist.star_nickname = nickname.strip()
            exist.bind_time = datetime.now()
        else:
            bind = QqBind(qq=qq, star_nickname=nickname.strip())
            session.add(bind)

    return True, f"""✅ 绑定成功！
星球昵称：{nickname}
已解锁全部VIP指令"""


def get_bind_info(qq: str) -> Optional[Dict]:
    """获取 QQ 绑定信息"""
    db = get_db()
    with db.session_scope() as session:
        bind = session.query(QqBind).filter(
            QqBind.qq == qq
        ).first()

        if not bind:
            return None

        return {
            "qq": bind.qq,
            "nickname": bind.star_nickname,
            "bind_time": bind.bind_time.strftime("%Y-%m-%d %H:%M") if bind.bind_time else None,
        }


def is_vip(qq: str) -> bool:
    """检查 QQ 号是否为 VIP"""
    bind_info = get_bind_info(qq)
    if not bind_info:
        return False

    return is_vip_by_nickname(bind_info["nickname"])


def check_free_limit(qq: str) -> Tuple[bool, int]:
    """检查免费次数，返回 (是否允许, 已用次数)"""
    db = get_db()
    today = date.today()

    with db.session_scope() as session:
        usage = session.query(FreeUsage).filter(
            and_(
                FreeUsage.qq == qq,
                FreeUsage.date == today
            )
        ).first()

        used = usage.count if usage else 0

        if used >= FREE_DAILY_LIMIT:
            return False, used

        if usage:
            usage.count += 1
        else:
            new_usage = FreeUsage(qq=qq, date=today, count=1)
            session.add(new_usage)

    return True, used


def get_free_usage(qq: str) -> int:
    """获取今日免费使用次数"""
    db = get_db()
    today = date.today()

    with db.session_scope() as session:
        usage = session.query(FreeUsage).filter(
            and_(
                FreeUsage.qq == qq,
                FreeUsage.date == today
            )
        ).first()

        return usage.count if usage else 0


def clean_expired_vips():
    """清理过期的 VIP（可选定时任务）"""
    db = get_db()
    today = date.today()

    with db.session_scope() as session:
        expired = session.query(ZsxqMember).filter(
            and_(
                ZsxqMember.expire_date != None,
                ZsxqMember.expire_date < today,
                ZsxqMember.status == True
            )
        ).all()

        for member in expired:
            member.status = False
            logger.info(f"VIP 已过期: {member.nickname}")

        return len(expired)


if __name__ == "__main__":
    print(f"VIP 总数: {get_vip_count()}")
    print(f"VIP 列表: {get_vip_list()[:10]}")
