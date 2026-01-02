from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, select
from models import Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/archive")
async def get_archive(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Post))
    posts = result.scalars().all()
    archive = {}
    for post in posts:
        year = post.date.year
        archive.setdefault(year, []).append({"id": post.id, "title": post.title, "date": post.date.strftime("%Y-%m-%d")})
    arr = []
    for year, posts in archive.items():
        arr.append({"year": year, "posts": posts})
    arr.sort(key=lambda x: x["year"], reverse=True)
    return JSONResponse(content={
        "code": 200,
        "data": {"archive": arr},
        "msg": "success"
    })