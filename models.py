from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import date, datetime, timezone

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
    created_at = Column(Date, default=date.today)

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    summary = Column(String(512))
    content = Column(Text)
    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="posts")
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")
    date = Column(Date, default=date.today)
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

class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    post = relationship("Post", backref="comments")
    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    parent = relationship("Comment", remote_side=[id], backref="replies")
    author_name = Column(String(128), nullable=False)
    author_email = Column(String(256), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User")