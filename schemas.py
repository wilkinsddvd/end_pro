from pydantic import BaseModel
from typing import List, Optional

class PostOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    content: str
    date: str
    author: str
    views: int

class PostListOut(BaseModel):
    page: int
    size: int
    total: int
    posts: List[PostOut]

class SiteInfoOut(BaseModel):
    title: str
    description: str
    icp: str
    footer: str

class MenuOut(BaseModel):
    title: str
    path: Optional[str] = None
    url: Optional[str] = None

class MenuListOut(BaseModel):
    menus: List[MenuOut]

class UserOut(BaseModel):
    id: int
    username: str

class MsgOut(BaseModel):
    code: int
    data: dict
    msg: str

# Ticket Schemas
class TicketCreate(BaseModel):
    """创建工单的请求模型"""
    title: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    priority: Optional[str] = "medium"  # low, medium, high, urgent

class TicketOut(BaseModel):
    """工单详情输出模型"""
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    priority: str
    status: str
    created_at: str
    user: Optional[str] = None

class TicketListOut(BaseModel):
    """工单列表输出模型"""
    page: int
    size: int
    total: int
    tickets: List[TicketOut]

# Quick Reply Schemas
class QuickReplyCreate(BaseModel):
    """创建快速回复的请求模型"""
    title: str
    content: str
    category: Optional[str] = ""

class QuickReplyOut(BaseModel):
    """快速回复详情输出模型"""
    id: int
    title: str
    content: str
    category: Optional[str]
    use_count: int
    created_at: str

class QuickReplyListOut(BaseModel):
    """快速回复列表输出模型"""
    page: int
    size: int
    total: int
    quick_replies: List[QuickReplyOut]