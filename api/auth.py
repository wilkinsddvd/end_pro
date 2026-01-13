from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from schemas import UserRegister, UserLogin, TokenResponse, UserOut
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.auth import get_password_hash, verify_password, create_access_token
from utils.dependencies import get_current_user

router = APIRouter()

@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_async_db)):
    """Register a new user"""
    try:
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": None, "msg": "用户名已存在"}
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(username=user_data.username, password_hash=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "data": {"id": user.id, "username": user.username},
                "msg": "注册成功"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": None, "msg": str(e)}
        )

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Login and get JWT token"""
    try:
        # Find user
        result = await db.execute(select(User).where(User.username == user_data.username))
        user = result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "msg": "用户名或密码错误"}
            )
        
        # Verify password
        if not verify_password(user_data.password, user.password_hash):
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "msg": "用户名或密码错误"}
            )
        
        # Generate token
        token = create_access_token(data={"sub": str(user.id)})
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "data": {
                    "token": token,
                    "user": {"id": user.id, "username": user.username}
                },
                "msg": "登录成功"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": None, "msg": str(e)}
        )

@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return JSONResponse(
        status_code=200,
        content={"code": 200, "data": {}, "msg": "logout success"}
    )

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """Get current user info"""
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "data": {}, "msg": "not authenticated"}
        )
    
    return JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "data": {"id": current_user.id, "username": current_user.username},
            "msg": "success"
        }
    )