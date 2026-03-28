# -*- coding: utf-8 -*-
"""
===================================
知识星球会员模型
===================================
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ZsxqMember(Base):
    """知识星球会员表"""
    __tablename__ = "zsxq_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_no = Column(Integer, nullable=True, comment="成员编号")
    user_id = Column(String(64), nullable=True, index=True, comment="用户加密id")
    nickname = Column(String(255), nullable=False, index=True, comment="用户昵称")
    wechat_nickname = Column(String(255), nullable=True, comment="微信昵称")
    card_nickname = Column(String(255), nullable=True, comment="星球名片昵称")
    remark_nickname = Column(String(255), nullable=True, comment="星球内备注昵称")
    zhishihao = Column(String(64), nullable=True, comment="知识号")
    phone = Column(String(32), nullable=True, comment="手机号码")
    wechat = Column(String(64), nullable=True, comment="微信号")
    identity = Column(String(32), nullable=True, comment="身份(星主/管理员/成员)")
    is_paid = Column(Boolean, nullable=False, default=False, comment="是否付费加入")
    join_date = Column(Date, nullable=True, comment="首次加入时间")
    source = Column(String(64), nullable=True, comment="首次来源")
    expire_date = Column(Date, nullable=True, comment="到期时间")
    days_to_renew = Column(Integer, nullable=True, comment="距离可续期的天数")
    renew_count = Column(Integer, nullable=True, default=0, comment="已续期次数")
    last_active_time = Column(DateTime, nullable=True, comment="最后活跃时间")
    total_paid = Column(Float, nullable=True, default=0.0, comment="成功付费的总金额")
    is_blocked = Column(Boolean, nullable=False, default=False, comment="是否被拉黑")
    is_quit = Column(Boolean, nullable=False, default=False, comment="是否退出星球")
    is_followed = Column(Boolean, nullable=False, default=False, comment="是否关注公众号")
    notify_enabled = Column(Boolean, nullable=False, default=True, comment="是否开启消息通知")
    fans_count = Column(Integer, nullable=True, default=0, comment="粉丝数")
    topics_count = Column(Integer, nullable=True, default=0, comment="主题数")
    comments_count = Column(Integer, nullable=True, default=0, comment="评论数")
    questions_count = Column(Integer, nullable=True, default=0, comment="提问数")
    question_amount = Column(Float, nullable=True, default=0.0, comment="提问金额")
    answers_count = Column(Integer, nullable=True, default=0, comment="回答数")
    answer_income = Column(Float, nullable=True, default=0.0, comment="回答收入")
    likes_given = Column(Integer, nullable=True, default=0, comment="点赞数")
    likes_received = Column(Integer, nullable=True, default=0, comment="获赞数")
    reward_given = Column(Float, nullable=True, default=0.0, comment="赞赏金额")
    reward_received = Column(Float, nullable=True, default=0.0, comment="获得赞赏金额")
    share_users = Column(Integer, nullable=True, default=0, comment="普通分享带来的用户数")
    share_amount = Column(Float, nullable=True, default=0.0, comment="普通分享带来的金额")
    share_reward_users = Column(Integer, nullable=True, default=0, comment="分享有赏带来的用户数")
    share_reward_orders = Column(Integer, nullable=True, default=0, comment="分享有赏带来的订单数")
    share_reward_amount = Column(Float, nullable=True, default=0.0, comment="分享有赏带来的金额")
    status = Column(Boolean, nullable=False, default=True, comment="状态: True=有效, False=无效")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<ZsxqMember(nickname={self.nickname}, identity={self.identity})>"
