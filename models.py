from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
import datetime

# Migration note: `create_all` will not add new tables to an existing database.
# New DBs will have ticket_history created automatically.
# For existing DBs, run:
#   CREATE TABLE ticket_history (
#       id INTEGER PRIMARY KEY AUTOINCREMENT,
#       ticket_id INTEGER NOT NULL REFERENCES ticket(id),
#       old_status VARCHAR(32) NOT NULL,
#       new_status VARCHAR(32) NOT NULL,
#       operator VARCHAR(128),
#       changed_at DATE
#   );

post_tag = Table(
    'post_tag', Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id"))
)

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, index=True)
    password_hash = Column(String(256))
    created_at = Column(Date, default=datetime.date.today)
    # Extended profile fields (nullable for backward compatibility)
    # NOTE: SQLAlchemy create_all skips existing tables, so these columns won't be
    # added automatically to an existing database.
    # Dev: delete the DB file and restart. Prod: run ALTER TABLE manually.
    nickname = Column(String(64), nullable=True)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    avatar = Column(String(512), nullable=True)
    bio = Column(Text, nullable=True)
    theme = Column(String(16), default="light")
    language = Column(String(16), default="zh-CN")
    email_notification = Column(Integer, default=1)
    sms_notification = Column(Integer, default=0)
    system_notification = Column(Integer, default=1)
    profile_public = Column(Integer, default=1)
    show_email = Column(Integer, default=0)
    show_phone = Column(Integer, default=0)
    allow_search = Column(Integer, default=1)
    # Role field: "user" (default) or "staff". If adding to an existing DB, run:
    # ALTER TABLE user ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user';
    role = Column(String(32), default="user", nullable=False)

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    summary = Column(String(512))
    content = Column(Text)
    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="posts")
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")
    date = Column(Date, default=datetime.date.today)
    author_id = Column(Integer, ForeignKey("user.id"))
    author = relationship("User")
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    posts = relationship("Post", back_populates="category")

class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    posts = relationship("Post", secondary=post_tag, back_populates="tags")

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
    updated_at = Column(Date, default=datetime.date.today, onupdate=datetime.date.today)  # 更新时间
    due_date = Column(Date, nullable=True)  # 截止日期
    user_id = Column(Integer, ForeignKey("user.id"))  # 创建者
    assignee_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # 处理人
    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    replies = relationship("TicketReply", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", order_by="TicketHistory.changed_at")

class TicketHistory(Base):
    """工单状态变更历史"""
    __tablename__ = "ticket_history"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("ticket.id"), nullable=False)   # 所属工单
    old_status = Column(String(32), nullable=False)   # 变更前状态
    new_status = Column(String(32), nullable=False)   # 变更后状态
    operator = Column(String(128), nullable=True)     # 操作人用户名（记录时快照）
    changed_at = Column(Date, default=datetime.date.today)  # 变更日期

    ticket = relationship("Ticket", back_populates="history")

class TicketReply(Base):
    """工单回复模型"""
    __tablename__ = "ticket_reply"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False)  # 所属工单
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)  # 回复人
    content = Column(Text, nullable=False)  # 回复内容
    created_at = Column(Date, default=datetime.date.today)  # 创建时间
    ticket = relationship("Ticket", back_populates="replies")
    user = relationship("User", foreign_keys=[user_id])

class QuickReply(Base):
    """快速回复模型"""
    __tablename__ = "quick_reply"
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)  # 快速回复标题
    content = Column(Text, nullable=False)  # 快速回复内容
    category = Column(String(64))  # 快速回复分类
    use_count = Column(Integer, default=0)  # 使用次数
    created_at = Column(Date, default=datetime.date.today)  # 创建时间