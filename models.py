from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, index=True)
    password_hash = Column(String(256))
    role = Column(String(32), default="user", nullable=False)  # "user" or "admin"
    created_at = Column(Date, default=datetime.date.today)

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    summary = Column(String(512))
    content = Column(Text)
    date = Column(Date, default=datetime.date.today)
    author_id = Column(Integer, ForeignKey("user.id"))
    author = relationship("User")
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)

class SiteInfo(Base):
    __tablename__ = "siteinfo"
    id = Column(Integer, primary_key=True)
    title = Column(String(128))
    description = Column(String(512))
    icp = Column(String(64))
    footer = Column(String(256))

class Menu(Base):
    __tablename__ = "menu"
    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    path = Column(String(128), nullable=True)
    url = Column(String(256), nullable=True)

class Ticket(Base):
    """工单模型"""
    __tablename__ = "ticket"
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)  # 工单标题
    description = Column(Text)  # 工单描述
    category = Column(String(64))  # 工单分类
    priority = Column(String(32), default="medium")  # 优先级：low, medium, high, urgent
    status = Column(String(32), default="open")  # 状态：open, in_progress, resolved, closed
    created_at = Column(Date, default=datetime.date.today)  # 创建时间
    user_id = Column(Integer, ForeignKey("user.id"))  # 创建者
    user = relationship("User")

class QuickReply(Base):
    """快速回复模型"""
    __tablename__ = "quick_reply"
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)  # 快速回复标题
    content = Column(Text, nullable=False)  # 快速回复内容
    category = Column(String(64))  # 快速回复分类
    use_count = Column(Integer, default=0)  # 使用次数
    created_at = Column(Date, default=datetime.date.today)  # 创建时间
    user_id = Column(Integer, ForeignKey("user.id"))  # 创建者
    user = relationship("User")

class TicketHistory(Base):
    """工单历史/审计日志模型 - 记录状态变更"""
    __tablename__ = "ticket_history"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("ticket.id"), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    old_status = Column(String(32))
    new_status = Column(String(32))
    note = Column(String(512))
    changed_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())
    ticket = relationship("Ticket")
    changed_by = relationship("User")