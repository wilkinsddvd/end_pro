from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
import datetime

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
    user_id = Column(Integer, ForeignKey("user.id"))  # 创建者
    user = relationship("User")