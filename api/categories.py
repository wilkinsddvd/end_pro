from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from models import Category, Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    cat_list = []
    for c in categories:
        count = await db.execute(select(func.count(Post.id)).where(Post.category_id == c.id))
        cnt = count.scalar()
        cat_list.append({"name": c.name, "count": cnt})
    return JSONResponse(content={
        "code": 200,
        "data": {"categories": cat_list},
        "msg": "success"
    })