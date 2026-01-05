from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from db import get_async_db
from fastapi.responses import JSONResponse
import hashlib

router = APIRouter()

def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login")
async def login(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code":400,"data":{},"msg":"username/password required"})
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar()
    if not user or user.password_hash != hash_pwd(password):
        return JSONResponse(content={"code":401,"data":{},"msg":"invalid credentials"})
    # 此处应生成 JWT，简化为 user_id 返回
    return JSONResponse(content={"code":200,"data":{"id":user.id,"username":user.username},"msg":"login success"})

@router.post("/register")
async def register(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code":400,"data":{},"msg":"username/password required"})
    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar():
        return JSONResponse(content={"code":409,"data":{},"msg":"username was taken"})
    user = User(username=username, password_hash=hash_pwd(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return JSONResponse(content={"code":201,"data":{"id":user.id,"username":user.username},"msg":"register success"})

@router.post("/logout")
async def logout():
    # 若使用JWT，前端可自行丢弃token
    return JSONResponse(content={"code":200,"data":{},"msg":"logout success"})

@router.get("/self")
async def get_self(user_id: int = 1):
    # 简化演示
    return JSONResponse(content={"code":200,"data":{"id":user_id,"username":"wilkinsddvd"},"msg":"whoami"})