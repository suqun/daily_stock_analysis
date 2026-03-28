# -*- coding: utf-8 -*-
"""
===================================
VIP 用户权限模型
===================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class QqBind(Base):
    """QQ 绑定表"""
    __tablename__ = "qq_binds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    qq = Column(String(32), nullable=False, unique=True, index=True, comment="QQ号")
    star_nickname = Column(String(255), nullable=False, comment="星球昵称")
    bind_time = Column(DateTime, nullable=False, default=datetime.now, comment="绑定时间")

    def __repr__(self):
        return f"<QqBind(qq={self.qq}, nickname={self.star_nickname})>"


class FreeUsage(Base):
    """免费使用次数表"""
    __tablename__ = "free_usages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    qq = Column(String(32), nullable=False, comment="QQ号")
    date = Column(Date, nullable=False, comment="日期")
    count = Column(Integer, nullable=False, default=0, comment="使用次数")

    def __repr__(self):
        return f"<FreeUsage(qq={self.qq}, date={self.date}, count={self.count})>"
