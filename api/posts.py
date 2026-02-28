import datetime
from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models import Post, User
from schemas import PostOut, PostCreate, PostUpdate
from db import get_async_db
from auth_utils import get_current_user
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload

router = APIRouter()


def _post_to_dict(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary or "",
        "content": post.content,
        "date": post.date.strftime("%Y-%m-%d") if post.date else "",
        "author": post.author.username if post.author else "",
        "views": post.views,
    }


@router.get("/posts")
async def list_posts(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        date: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """List posts belonging to the current user with optional search/date filters."""
    base_stmt = select(Post).where(Post.author_id == current_user.id)
    if search:
        base_stmt = base_stmt.where(
            Post.title.contains(search) | Post.summary.contains(search) | Post.content.contains(search)
        )
    if date:
        base_stmt = base_stmt.where(Post.date == date)

    # COUNT using SQL aggregate – avoids loading all rows
    count_stmt = select(func.count()).select_from(Post).where(Post.author_id == current_user.id)
    if search:
        count_stmt = count_stmt.where(
            Post.title.contains(search) | Post.summary.contains(search) | Post.content.contains(search)
        )
    if date:
        count_stmt = count_stmt.where(Post.date == date)
    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar()

    stmt = base_stmt.order_by(Post.date.desc()).offset((page - 1) * size).limit(size)
    stmt = stmt.options(selectinload(Post.author))
    result = await db.execute(stmt)
    posts = result.scalars().all()

    return JSONResponse(content={
        "code": 200,
        "data": {
            "page": page,
            "size": size,
            "total": total_count,
            "posts": [_post_to_dict(p) for p in posts],
        },
        "msg": "success"
    })


@router.get("/posts/{id}")
async def get_post(
        id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """Get a single post belonging to the current user."""
    stmt = (
        select(Post)
        .where(Post.id == id)
        .where(Post.author_id == current_user.id)
        .options(selectinload(Post.author))
    )
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "post not found"})
    return JSONResponse(content={"code": 200, "data": _post_to_dict(post), "msg": "success"})


@router.post("/posts")
async def create_post(
        data: PostCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """Create a new post for the current user."""
    post_date = None
    if data.date:
        try:
            post_date = datetime.date.fromisoformat(data.date)
        except ValueError:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "invalid date format, use YYYY-MM-DD"})

    post = Post(
        title=data.title,
        summary=data.summary or "",
        content=data.content,
        date=post_date or datetime.date.today(),
        author_id=current_user.id,
        views=0,
        likes=0,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # Reload with author
    stmt = select(Post).where(Post.id == post.id).options(selectinload(Post.author))
    result = await db.execute(stmt)
    post = result.scalar_one()
    return JSONResponse(content={"code": 201, "data": _post_to_dict(post), "msg": "post created successfully"})


@router.put("/posts/{id}")
async def update_post(
        id: int,
        data: PostUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """Update a post belonging to the current user."""
    stmt = select(Post).where(Post.id == id).where(Post.author_id == current_user.id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "post not found"})

    if data.title is not None:
        post.title = data.title
    if data.summary is not None:
        post.summary = data.summary
    if data.content is not None:
        post.content = data.content
    if data.date is not None:
        try:
            post.date = datetime.date.fromisoformat(data.date)
        except ValueError:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "invalid date format, use YYYY-MM-DD"})

    await db.commit()
    await db.refresh(post)

    stmt = select(Post).where(Post.id == post.id).options(selectinload(Post.author))
    result = await db.execute(stmt)
    post = result.scalar_one()
    return JSONResponse(content={"code": 200, "data": _post_to_dict(post), "msg": "post updated successfully"})


@router.delete("/posts/{id}")
async def delete_post(
        id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """Delete a post belonging to the current user."""
    stmt = select(Post).where(Post.id == id).where(Post.author_id == current_user.id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "post not found"})
    await db.delete(post)
    await db.commit()
    return JSONResponse(content={"code": 200, "data": {}, "msg": "post deleted successfully"})
