from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from models import Category, Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

# ... 省略前略 ...
@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_async_db)):
    try:
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
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})