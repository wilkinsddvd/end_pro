from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import Tag, Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/tags")
async def get_tags(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    tag_list = []
    for t in tags:
        tag_list.append({"name": t.name, "count": len(t.posts)})
    return JSONResponse(content={
        "code": 200,
        "data": {"tags": tag_list},
        "msg": "success"
    })