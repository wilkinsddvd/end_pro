from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Tag
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/tags")
async def get_tags(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Tag).options(selectinload(Tag.posts))
        result = await db.execute(stmt)
        tags = result.scalars().all()
        tag_list = []
        for t in tags:
            tag_list.append({"name": t.name, "count": len(t.posts) if t.posts else 0})
        return JSONResponse(content={
            "code": 200,
            "data": {"tags": tag_list},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})