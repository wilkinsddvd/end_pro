from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import Post
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/posts/{id}/view")
async def add_view(id: int, db: AsyncSession = Depends(get_async_db)):
    post = await db.get(Post, id)
    if not post:
        return JSONResponse(content={"code":404,"data":{},"msg":"post not found"})
    post.views += 1
    db.add(post)
    await db.commit()
    return JSONResponse(content={"code":200,"data":{},"msg":"view +1"})

@router.post("/posts/{id}/like")
async def add_like(id: int, db: AsyncSession = Depends(get_async_db)):
    post = await db.get(Post, id)
    if not post:
        return JSONResponse(content={"code":404,"data":{},"msg":"post not found"})
    post.likes += 1
    db.add(post)
    await db.commit()
    return JSONResponse(content={"code":200,"data":{},"msg":"like +1"})