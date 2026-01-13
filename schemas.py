from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# ============ User Schemas ============
class UserOut(BaseModel):
    id: int
    username: str

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)

class UserLogin(BaseModel):
    username: str
    password: str = Field(..., max_length=72)

class TokenResponse(BaseModel):
    token: str
    user: UserOut

# ============ Post Schemas ============
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    summary: Optional[str] = Field(None, max_length=512)
    content: str
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = []

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    summary: Optional[str] = Field(None, max_length=512)
    content: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

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
    likes: int = 0

class PostListOut(BaseModel):
    page: int
    size: int
    total: int
    posts: List[PostOut]

# ============ Category Schemas ============
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

class CategoryOut(BaseModel):
    id: int
    name: str
    count: int

class CategoryListOut(BaseModel):
    categories: List[CategoryOut]

# ============ Tag Schemas ============
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

class TagUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

class TagOut(BaseModel):
    id: int
    name: str
    count: int

class TagListOut(BaseModel):
    tags: List[TagOut]

# ============ Comment Schemas ============
class CommentCreate(BaseModel):
    post_id: int
    parent_id: Optional[int] = None
    author_name: str = Field(..., min_length=1, max_length=128)
    author_email: Optional[EmailStr] = None
    content: str = Field(..., min_length=1)

class CommentOut(BaseModel):
    id: int
    post_id: int
    parent_id: Optional[int]
    author_name: str
    author_email: Optional[str]
    content: str
    created_at: str
    replies: Optional[List['CommentOut']] = []

# Enable forward references
CommentOut.model_rebuild()

class CommentListOut(BaseModel):
    comments: List[CommentOut]

# ============ Archive Schemas ============
class ArchivePost(BaseModel):
    id: int
    title: str
    date: str

class ArchiveYear(BaseModel):
    year: int
    posts: List[ArchivePost]

class ArchiveTreeOut(BaseModel):
    archive: List[ArchiveYear]

# ============ SiteInfo Schemas ============
class SiteInfoOut(BaseModel):
    title: str
    description: str
    icp: str
    footer: str

# ============ Menu Schemas ============
class MenuOut(BaseModel):
    id: int
    title: str
    path: Optional[str] = None
    url: Optional[str] = None

class MenuListOut(BaseModel):
    menus: List[MenuOut]

# ============ Common Response Schemas ============
class MsgOut(BaseModel):
    code: int
    data: dict
    msg: str

# ============ Ticket Category Schemas ============
class TicketCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=256)

class TicketCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=256)

class TicketCategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    count: int

class TicketCategoryListOut(BaseModel):
    categories: List[TicketCategoryOut]

# ============ Ticket Schemas ============
class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    status: Optional[str] = Field("open", pattern="^(open|in_progress|resolved|closed)$")
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high|urgent)$")
    category_id: Optional[int] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    category_id: Optional[int] = None

class TicketOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    category_id: Optional[int]
    category_name: Optional[str]
    user_id: Optional[int]
    username: Optional[str]
    created_at: str
    updated_at: str

class TicketListOut(BaseModel):
    page: int
    size: int
    total: int
    tickets: List[TicketOut]

# ============ Quick Reply Schemas ============
class QuickReplyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., min_length=1)

class QuickReplyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    content: Optional[str] = Field(None, min_length=1)

class QuickReplyOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: str
    updated_at: str

class QuickReplyListOut(BaseModel):
    quick_replies: List[QuickReplyOut]