from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Tag, User
from schemas import TagCreate, TagUpdate
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.dependencies import require_current_user

router = APIRouter()

@router.get("/tags")
async def get_tags(db: AsyncSession = Depends(get_async_db)):
    """Get all tags with post counts"""
    try:
        stmt = select(Tag).options(selectinload(Tag.posts))
        result = await db.execute(stmt)
        tags = result.scalars().all()
        tag_list = []
        for t in tags:
            tag_list.append({
                "id": t.id,
                "name": t.name,
                "count": len(t.posts) if t.posts else 0
            })
        return JSONResponse(content={
            "code": 200,
            "data": {"tags": tag_list},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.post("/tags")
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new tag (requires authentication)"""
    try:
        # Check if tag already exists
        result = await db.execute(select(Tag).where(Tag.name == tag_data.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": {}, "msg": "tag already exists"}
            )
        
        tag = Tag(name=tag_data.name)
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": {"id": tag.id, "name": tag.name, "count": 0},
                "msg": "tag created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.put("/tags/{id}")
async def update_tag(
    id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a tag (requires authentication)"""
    try:
        result = await db.execute(select(Tag).where(Tag.id == id))
        tag = result.scalar_one_or_none()
        
        if not tag:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "tag not found"}
            )
        
        # Check if new name already exists
        name_check = await db.execute(
            select(Tag).where(Tag.name == tag_data.name, Tag.id != id)
        )
        if name_check.scalar_one_or_none():
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": {}, "msg": "tag name already exists"}
            )
        
        tag.name = tag_data.name
        await db.commit()
        
        # Reload with posts to get count
        stmt = select(Tag).where(Tag.id == id).options(selectinload(Tag.posts))
        result = await db.execute(stmt)
        tag = result.scalar_one()
        
        return JSONResponse(content={
            "code": 200,
            "data": {"id": tag.id, "name": tag.name, "count": len(tag.posts) if tag.posts else 0},
            "msg": "tag updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.delete("/tags/{id}")
async def delete_tag(
    id: int,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a tag (requires authentication)"""
    try:
        # Get tag with posts
        stmt = select(Tag).where(Tag.id == id).options(selectinload(Tag.posts))
        result = await db.execute(stmt)
        tag = result.scalar_one_or_none()
        
        if not tag:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "tag not found"}
            )
        
        # Check if tag has posts
        if tag.posts and len(tag.posts) > 0:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": {}, "msg": "tag has posts, cannot delete"}
            )
        
        await db.delete(tag)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "tag deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )