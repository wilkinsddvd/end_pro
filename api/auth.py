from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from db import get_async_db
from fastapi.responses import JSONResponse
from api.deps import create_access_token, get_current_user_id
import hashlib

router = APIRouter()

def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login")
async def login(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar()
    if not user or user.password_hash != hash_pwd(password):
        return JSONResponse(content={"code": 401, "data": {}, "msg": "invalid credentials"})
    # 生成 JWT Token，sub 存储 user_id（字符串形式）
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return JSONResponse(content={
        "code": 200,
        "data": {"id": user.id, "username": user.username, "token": token},
        "msg": "login success"
    })

@router.post("/register")
async def register(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})
    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar():
        return JSONResponse(content={"code": 409, "data": {}, "msg": "username was taken"})
    user = User(username=username, password_hash=hash_pwd(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    # 注册成功后同样返回 token，前端可直接登录
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return JSONResponse(content={
        "code": 201,
        "data": {"id": user.id, "username": user.username, "token": token},
        "msg": "register success"
    })

@router.post("/logout")
async def logout():
    # JWT 无状态，前端丢弃 token 即可
    return JSONResponse(content={"code": 200, "data": {}, "msg": "logout success"})

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_async_db)):
    """获取所有用户列表（供工单处理人下拉选择使用）"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return JSONResponse(content={
        "code": 200,
        "data": {"users": [{"id": u.id, "username": u.username} for u in users]},
        "msg": "success"
    })

@router.get("/self")
async def get_self(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取当前登录用户信息（需要 JWT 认证）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})
    return JSONResponse(content={
        "code": 200,
        "data": {"id": user.id, "username": user.username},
        "msg": "success"
    })