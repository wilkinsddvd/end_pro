from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from schemas import UserRegister, UserLogin, TokenResponse, UserOut
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.auth import get_password_hash, verify_password, create_access_token
from utils.dependencies import get_current_user
import logging

router = APIRouter()

@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_async_db)):
    """Register a new user"""
    try:
        # Explicit password length validation
        if len(user_data.password) > 72:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": None, "msg": "密码长度不能超过72个字符"}
            )
        
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": None, "msg": "用户名已存在"}
            )
        
        # Create new user with password hashing
        try:
            hashed_password = get_password_hash(user_data.password)
        except ValueError as hash_error:
            # Catch password hashing errors
            logging.error(f"Password hashing error during registration: {str(hash_error)}")
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": None, "msg": "密码格式不正确或超出允许长度"}
            )
        
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
    except ValueError as ve:
        # Handle validation errors
        logging.error(f"Validation error during registration: {str(ve)}")
        return JSONResponse(
            status_code=400,
            content={"code": 400, "data": None, "msg": f"参数验证失败: {str(ve)}"}
        )
    except Exception as e:
        # Log the error for debugging but return generic message
        logging.error(f"Unexpected registration error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": None, "msg": "注册失败，请稍后重试"}
        )

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Login and get JWT token"""
    try:
        # Explicit password length validation
        if len(user_data.password) > 72:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": None, "msg": "密码长度不能超过72个字符"}
            )
        
        # Find user
        result = await db.execute(select(User).where(User.username == user_data.username))
        user = result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "msg": "用户名或密码错误"}
            )
        
        # Verify password with error handling
        try:
            password_valid = verify_password(user_data.password, user.password_hash)
        except ValueError as verify_error:
            # Catch password verification errors
            logging.error(f"Password verification error during login: {str(verify_error)}")
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": None, "msg": "密码格式不正确或超出允许长度"}
            )
        
        if not password_valid:
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
    except ValueError as ve:
        # Handle validation errors
        logging.error(f"Validation error during login: {str(ve)}")
        return JSONResponse(
            status_code=400,
            content={"code": 400, "data": None, "msg": f"参数验证失败: {str(ve)}"}
        )
    except Exception as e:
        # Log the error for debugging but return generic message
        logging.error(f"Unexpected login error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": None, "msg": "登录失败，请稍后重试"}
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