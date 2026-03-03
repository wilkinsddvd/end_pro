from pydantic import BaseModel
from typing import List, Optional

class PostOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    content: str
    category: str
    tags: List[str]
    date: str
    author: str
    views: int

class PostListOut(BaseModel):
    page: int
    size: int
    total: int
    posts: List[PostOut]

class CategoryOut(BaseModel):
    name: str
    count: int

class CategoryListOut(BaseModel):
    categories: List[CategoryOut]

class TagOut(BaseModel):
    name: str
    count: int

class TagListOut(BaseModel):
    tags: List[TagOut]

class ArchivePost(BaseModel):
    id: int
    title: str
    date: str

class ArchiveYear(BaseModel):
    year: int
    posts: List[ArchivePost]

class ArchiveTreeOut(BaseModel):
    archive: List[ArchiveYear]

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
    due_date: Optional[str] = None       # 截止日期，格式 YYYY-MM-DD
    assignee_id: Optional[int] = None    # 处理人 ID

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
    due_date: Optional[str] = None       # 截止日期，格式 YYYY-MM-DD
    assignee: Optional[str] = None       # 处理人用户名
    assignee_id: Optional[int] = None    # 处理人 ID
    is_overdue: Optional[bool] = False   # 是否逾期标记
    updated_at: Optional[str] = None     # 更新时间

class TicketListOut(BaseModel):
    """工单列表输出模型"""
    page: int
    size: int
    total: int
    tickets: List[TicketOut]

class TicketHistoryOut(BaseModel):
    """工单状态变更历史输出模型"""
    id: int
    ticket_id: int
    old_status: str
    new_status: str
    operator: Optional[str] = None
    changed_at: str

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