from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Post, Category, Tag, User
from schemas import PostOut, PostCreate, PostUpdate
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from utils.dependencies import require_current_user


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
    """List posts with optional filtering"""
    try:
        # Build query with eager loading
        stmt = select(Post).options(
            selectinload(Post.category),
            selectinload(Post.tags),
            selectinload(Post.author)
        )
        
        # Apply filters
        if search:
            stmt = stmt.where(
                Post.title.contains(search) | 
                Post.summary.contains(search) | 
                Post.content.contains(search)
            )
        if category:
            stmt = stmt.join(Category).where(Category.name == category)
        if tag:
            stmt = stmt.join(Post.tags).where(Tag.name == tag)
        if date:
            stmt = stmt.where(Post.date == date)
        
        stmt = stmt.order_by(Post.date.desc())

        # Get total count
        count_result = await db.execute(select(Post).where(stmt.whereclause) if stmt.whereclause else select(Post))
        total_count = len(count_result.scalars().all())
        
        # Apply pagination
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await db.execute(stmt)
        posts = result.scalars().all()
        
        # Build response
        post_list = []
        for post in posts:
            post_list.append({
                "id": post.id,
                "title": post.title,
                "summary": post.summary,
                "content": post.content,
                "category": post.category.name if post.category else "",
                "tags": [t.name for t in post.tags] if post.tags else [],
                "date": post.date.strftime("%Y-%m-%d") if post.date else "",
                "author": post.author.username if post.author else "",
                "views": post.views,
                "likes": post.likes
            })
            
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
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.get("/posts/{id}")
async def get_post(id: int, db: AsyncSession = Depends(get_async_db)):
    """Get a single post by ID"""
    try:
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
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "post not found"}
            )
            
        data = {
            "id": post.id,
            "title": post.title,
            "summary": post.summary,
            "content": post.content,
            "category": post.category.name if post.category else "",
            "tags": [t.name for t in post.tags] if post.tags else [],
            "date": post.date.strftime('%Y-%m-%d') if post.date else "",
            "author": post.author.username if post.author else "",
            "views": post.views,
            "likes": post.likes
        }
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new post (requires authentication)"""
    try:
        # Create post
        post = Post(
            title=post_data.title,
            summary=post_data.summary,
            content=post_data.content,
            category_id=post_data.category_id,
            author_id=current_user.id
        )
        
        # Add tags if provided
        if post_data.tag_ids:
            tag_result = await db.execute(select(Tag).where(Tag.id.in_(post_data.tag_ids)))
            tags = tag_result.scalars().all()
            post.tags = tags
        
        db.add(post)
        await db.commit()
        await db.refresh(post)
        
        # Load relationships
        await db.refresh(post, ['category', 'tags', 'author'])
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": {
                    "id": post.id,
                    "title": post.title,
                    "summary": post.summary,
                    "content": post.content,
                    "category": post.category.name if post.category else "",
                    "tags": [t.name for t in post.tags] if post.tags else [],
                    "date": post.date.strftime('%Y-%m-%d') if post.date else "",
                    "author": post.author.username if post.author else "",
                    "views": post.views,
                    "likes": post.likes
                },
                "msg": "post created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.put("/posts/{id}")
async def update_post(
    id: int,
    post_data: PostUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a post (requires authentication)"""
    try:
        # Get post
        result = await db.execute(select(Post).where(Post.id == id))
        post = result.scalar_one_or_none()
        
        if not post:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "post not found"}
            )
        
        # Check ownership
        if post.author_id != current_user.id:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "data": {}, "msg": "not authorized"}
            )
        
        # Update fields
        if post_data.title is not None:
            post.title = post_data.title
        if post_data.summary is not None:
            post.summary = post_data.summary
        if post_data.content is not None:
            post.content = post_data.content
        if post_data.category_id is not None:
            post.category_id = post_data.category_id
        if post_data.tag_ids is not None:
            tag_result = await db.execute(select(Tag).where(Tag.id.in_(post_data.tag_ids)))
            tags = tag_result.scalars().all()
            post.tags = tags
        
        await db.commit()
        await db.refresh(post, ['category', 'tags', 'author'])
        
        return JSONResponse(content={
            "code": 200,
            "data": {
                "id": post.id,
                "title": post.title,
                "summary": post.summary,
                "content": post.content,
                "category": post.category.name if post.category else "",
                "tags": [t.name for t in post.tags] if post.tags else [],
                "date": post.date.strftime('%Y-%m-%d') if post.date else "",
                "author": post.author.username if post.author else "",
                "views": post.views,
                "likes": post.likes
            },
            "msg": "post updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.delete("/posts/{id}")
async def delete_post(
    id: int,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a post (requires authentication)"""
    try:
        result = await db.execute(select(Post).where(Post.id == id))
        post = result.scalar_one_or_none()
        
        if not post:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "post not found"}
            )
        
        # Check ownership
        if post.author_id != current_user.id:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "data": {}, "msg": "not authorized"}
            )
        
        await db.delete(post)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "post deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )