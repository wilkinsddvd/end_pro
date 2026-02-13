from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Post, User
from schemas import PostOut
from db import get_async_db
from auth_utils import get_current_user
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload


router = APIRouter()


@router.get("/posts")
async def list_posts(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        date: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    # 构造动态筛选 - 只返回当前用户的文章
    stmt = select(Post).where(Post.author_id == current_user.id)
    if search:
        stmt = stmt.where(Post.title.contains(search) | Post.summary.contains(search) | Post.content.contains(search))
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


@router.get("/posts/{id}")
async def get_post(
        id: int, 
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    try:
        # 用 selectinload 防止 missing greenlet 问题
        stmt = (
            select(Post)
            .where(Post.id == id)
            .where(Post.author_id == current_user.id)  # 只能查看自己的文章
            .options(
                selectinload(Post.author),
            )
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "post not found"})
        author = post.author.username if post.author else ""
        data = {
            "id": post.id,
            "title": post.title,
            "summary": post.summary,
            "content": post.content,
            "date": post.date.strftime('%Y-%m-%d') if post.date else "",
            "author": author,
            "views": post.views
        }
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})