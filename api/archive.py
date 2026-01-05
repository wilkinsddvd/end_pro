from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/archive")
async def get_archive(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Post)
        result = await db.execute(stmt)
        posts = result.scalars().all()
        archive = {}
        for post in posts:
            year = post.date.year if post.date else 0
            archive.setdefault(year, []).append({
                "id": post.id,
                "title": post.title,
                "date": post.date.strftime("%Y-%m-%d") if post.date else ""
            })
        arr = []
        for year, plist in archive.items():
            arr.append({"year": year, "posts": plist})
        arr.sort(key=lambda x: x["year"], reverse=True)
        return JSONResponse(content={
            "code": 200,
            "data": {"archive": arr},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})