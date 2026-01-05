from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from models import Category, Post, User
from schemas import CategoryCreate, CategoryUpdate
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.dependencies import require_current_user

router = APIRouter()

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_async_db)):
    """Get all categories with post counts"""
    try:
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        cat_list = []
        for c in categories:
            count = await db.execute(select(func.count(Post.id)).where(Post.category_id == c.id))
            cnt = count.scalar()
            cat_list.append({"id": c.id, "name": c.name, "count": cnt})
        return JSONResponse(content={
            "code": 200,
            "data": {"categories": cat_list},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.post("/categories")
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new category (requires authentication)"""
    try:
        # Check if category already exists
        result = await db.execute(select(Category).where(Category.name == category_data.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": {}, "msg": "category already exists"}
            )
        
        category = Category(name=category_data.name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": {"id": category.id, "name": category.name, "count": 0},
                "msg": "category created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.put("/categories/{id}")
async def update_category(
    id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a category (requires authentication)"""
    try:
        result = await db.execute(select(Category).where(Category.id == id))
        category = result.scalar_one_or_none()
        
        if not category:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "category not found"}
            )
        
        # Check if new name already exists
        name_check = await db.execute(
            select(Category).where(Category.name == category_data.name, Category.id != id)
        )
        if name_check.scalar_one_or_none():
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": {}, "msg": "category name already exists"}
            )
        
        category.name = category_data.name
        await db.commit()
        await db.refresh(category)
        
        count = await db.execute(select(func.count(Post.id)).where(Post.category_id == category.id))
        cnt = count.scalar()
        
        return JSONResponse(content={
            "code": 200,
            "data": {"id": category.id, "name": category.name, "count": cnt},
            "msg": "category updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.delete("/categories/{id}")
async def delete_category(
    id: int,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a category (requires authentication)"""
    try:
        result = await db.execute(select(Category).where(Category.id == id))
        category = result.scalar_one_or_none()
        
        if not category:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "category not found"}
            )
        
        # Check if category has posts
        count = await db.execute(select(func.count(Post.id)).where(Post.category_id == id))
        if count.scalar() > 0:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": {}, "msg": "category has posts, cannot delete"}
            )
        
        await db.delete(category)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "category deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )