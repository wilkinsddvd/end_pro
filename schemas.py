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