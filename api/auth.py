import os
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from db import get_async_db
from fastapi.responses import JSONResponse
from auth_utils import create_access_token, get_current_user
import hashlib

router = APIRouter()

# ---------------------------------------------------------------------------
# CAPTCHA – pluggable stub; disabled by default for dev
# Enable by setting CAPTCHA_ENABLED=true in env; provide your own verify logic.
# ---------------------------------------------------------------------------
CAPTCHA_ENABLED = os.getenv("CAPTCHA_ENABLED", "false").lower() == "true"


def _verify_captcha(token: str) -> bool:
    """
    CAPTCHA verification stub.
    Replace with real provider (hCaptcha, reCAPTCHA, etc.) when CAPTCHA_ENABLED=true.
    When CAPTCHA_ENABLED=true but no real integration is configured, this returns False
    to prevent unintentional bypass.
    """
    if not CAPTCHA_ENABLED:
        return True
    # TODO: integrate with a real CAPTCHA provider (hCaptcha, reCAPTCHA, etc.)
    # Return False here so enabling CAPTCHA_ENABLED forces explicit integration
    return False


def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/login")
async def login(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    """
    User login. Returns JWT access token on success.
    Supports optional CAPTCHA check (enabled via CAPTCHA_ENABLED env var).
    """
    username = data.get("username")
    password = data.get("password")
    captcha_token = data.get("captcha_token", "")

    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})

    if CAPTCHA_ENABLED and not _verify_captcha(captcha_token):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "captcha verification failed"})

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar()
    if not user or user.password_hash != hash_pwd(password):
        return JSONResponse(content={"code": 401, "data": {}, "msg": "invalid credentials"})

    access_token = create_access_token(data={"sub": user.id, "username": user.username})

    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "token": access_token
        },
        "msg": "login success"
    })


@router.post("/register")
async def register(data: dict = Body(...), db: AsyncSession = Depends(get_async_db)):
    """
    User registration. New users are assigned the 'user' role by default.
    Supports optional CAPTCHA check (enabled via CAPTCHA_ENABLED env var).
    """
    username = data.get("username")
    password = data.get("password")
    captcha_token = data.get("captcha_token", "")

    if not username or not password:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username/password required"})

    if CAPTCHA_ENABLED and not _verify_captcha(captcha_token):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "captcha verification failed"})

    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar():
        return JSONResponse(content={"code": 409, "data": {}, "msg": "username was taken"})

    user = User(username=username, password_hash=hash_pwd(password), role="user")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return JSONResponse(content={
        "code": 201,
        "data": {"id": user.id, "username": user.username, "role": user.role},
        "msg": "register success"
    })


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless; client should discard the token
    return JSONResponse(content={"code": 200, "data": {}, "msg": "logout success"})


@router.get("/self")
async def get_self(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information, including role for client-side routing.
    Requires Authorization: Bearer <token> header.
    """
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
        },
        "msg": "whoami"
    })
