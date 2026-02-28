from pydantic import BaseModel, validator
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

class PostCreate(BaseModel):
    """创建文章请求模型"""
    title: str
    summary: Optional[str] = ""
    content: str
    date: Optional[str] = None

class PostUpdate(BaseModel):
    """更新文章请求模型"""
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    date: Optional[str] = None

class SiteInfoOut(BaseModel):
    title: str
    description: str
    icp: str
    footer: str

class SiteInfoUpdate(BaseModel):
    """更新站点信息请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    icp: Optional[str] = None
    footer: Optional[str] = None

class MenuOut(BaseModel):
    title: str
    path: Optional[str] = None
    url: Optional[str] = None

class MenuListOut(BaseModel):
    menus: List[MenuOut]

class UserOut(BaseModel):
    id: int
    username: str
    role: str = "user"

class MsgOut(BaseModel):
    code: int
    data: dict
    msg: str

# Ticket Schemas
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
VALID_STATUSES = ["open", "in_progress", "resolved", "closed"]

# Allowed status transitions: {from_status: [allowed_to_statuses]}
TICKET_TRANSITIONS = {
    "open": ["in_progress", "closed"],
    "in_progress": ["resolved", "open", "closed"],
    "resolved": ["closed", "open"],
    "closed": [],
}

class TicketCreate(BaseModel):
    """创建工单的请求模型"""
    title: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    priority: Optional[str] = "medium"  # low, medium, high, urgent

    @validator("priority")
    def validate_priority(cls, v):
        if v not in VALID_PRIORITIES:
            return "medium"
        return v

class TicketUpdate(BaseModel):
    """更新工单请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None  # 状态变更备注

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

class TicketHistoryOut(BaseModel):
    """工单历史记录输出模型"""
    id: int
    old_status: Optional[str]
    new_status: Optional[str]
    note: Optional[str]
    changed_by: str
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

# Stats Schemas
class UserStatsOut(BaseModel):
    """用户统计数据输出模型"""
    post_count: int
    ticket_counts: dict  # {status: count}
    quick_reply_count: int
    quick_reply_total_uses: int

class AdminStatsOut(BaseModel):
    """管理员全局统计数据输出模型"""
    total_users: int
    total_posts: int
    total_tickets: int
    total_quick_replies: int
    tickets_by_status: dict
    recent_7d: dict
    recent_30d: dict
