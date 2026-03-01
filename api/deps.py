from fastapi import Header, HTTPException
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Optional
import os

# JWT 配置（生产环境应从环境变量读取）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

def create_access_token(data: dict) -> str:
    """生成 JWT Token"""
    from datetime import datetime, timedelta, timezone
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """解码 JWT Token，返回 payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """
    FastAPI 依赖：从请求头 Authorization: Bearer <token> 中提取 user_id。
    供需要认证的路由使用。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token payload missing user id")
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user id in token")
