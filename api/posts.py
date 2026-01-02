from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Post, Category, Tag, User
from schemas import PostOut
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


router = APIRouter()


@router.get("/posts")
async def list_posts(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        date: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    # 构造动态筛选
    stmt = select(Post)
    if search:
        stmt = stmt.where(Post.title.contains(search) | Post.summary.contains(search) | Post.content.contains(search))
    if category:
        stmt = stmt.join(Category).where(Category.name == category)
    if tag:
        stmt = stmt.join(Post.tags).where(Tag.name == tag)
    if date:
        stmt = stmt.where(Post.date == date)
    stmt = stmt.order_by(Post.date.desc())

    total = await db.execute(stmt)
    total_count = len(total.scalars().all())
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    posts = result.scalars().all()
    post_list = []
    for post in posts:
        post_list.append(PostOut(
            id=post.id,
            title=post.title,
            summary=post.summary,
            content=post.content,
            category=post.category.name if post.category else "",
            tags=[t.name for t in post.tags],
            date=post.date.strftime("%Y-%m-%d"),
            author=post.author.username if post.author else "",
            views=post.views
        ).dict())
    return JSONResponse(content={
        "code": 200,
        "data": {
            "page": page,
            "size": size,
            "total": total_count,
            "posts": post_list
        },
        "msg": "success"
    })



router = APIRouter()

@router.get("/posts/{id}")
async def get_post(id: int, db: AsyncSession = Depends(get_async_db)):
    try:
        # 用 selectinload 防止 missing greenlet 问题
        stmt = (
            select(Post)
            .where(Post.id == id)
            .options(
                selectinload(Post.category),
                selectinload(Post.tags),
                selectinload(Post.author),
            )
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "post not found"})
        category = post.category.name if post.category else ""
        author = post.author.username if post.author else ""
        tags = [t.name for t in post.tags] if post.tags else []
        data = {
            "id": post.id,
            "title": post.title,
            "summary": post.summary,
            "content": post.content,
            "category": category,
            "tags": tags,
            "date": post.date.strftime('%Y-%m-%d') if post.date else "",
            "author": author,
            "views": post.views
        }
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})