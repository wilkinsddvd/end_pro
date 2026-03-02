from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from db import get_async_db
from fastapi.responses import JSONResponse
from api.deps import create_access_token, get_current_user_id, _token_blacklist, limiter
from passlib.context import CryptContext
from typing import Optional
from fastapi import Header
import re

router = APIRouter()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

def hash_pwd(password: str) -> str:
    # bcrypt 最多有效处理 72 字节，截断后再哈希，避免版本兼容性报错
    return _pwd_context.hash(password.encode("utf-8")[:72].decode("utf-8", errors="ignore"))

def verify_pwd(plain: str, hashed: str) -> bool:
    truncated = plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return _pwd_context.verify(truncated, hashed)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})
    if len(password) > 64:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "密码最长 64 位"})
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar()
    if not user or not verify_pwd(password, user.password_hash):
        return JSONResponse(content={"code": 401, "data": {}, "msg": "invalid credentials"})
    # 生成 JWT Token，sub 存储 user_id（字符串形式）
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return JSONResponse(content={
        "code": 200,
        "data": {"id": user.id, "username": user.username, "token": token},
        "msg": "login success"
    })

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})
    username = username.strip()
    if not username:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})
    if len(username) < 3 or len(username) > 32:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "用户名长度应在 3-32 字符之间"})
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "用户名只允许字母、数字和下划线"})
    if len(password) < 8:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "密码长度至少 8 位"})
    if len(password) > 64:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "密码最长 64 位"})
    if not (re.search(r'[A-Za-z]', password) and re.search(r'[0-9]', password)):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "密码需同时包含字母和数字"})
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
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        _token_blacklist.add(token)
    return JSONResponse(content={"code": 200, "data": {}, "msg": "logout success"})

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_async_db), user_id: int = Depends(get_current_user_id)):
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
    from api.user import _format_user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})
    return JSONResponse(content={"code": 200, "data": _format_user(user), "msg": "success"})