from fastapi import Header, HTTPException
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Optional
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# JWT 配置
# 生成强密钥：python -c "import secrets; print(secrets.token_hex(64))"
_jwt_secret = os.getenv("JWT_SECRET_KEY")
if not _jwt_secret:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(64))\""
    )
SECRET_KEY: str = _jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 速率限制器（slowapi）
limiter = Limiter(key_func=get_remote_address)

# 内存 Token 黑名单（单实例部署；多实例可替换为 Redis）
_token_blacklist: set = set()

def create_access_token(data: dict) -> str:
    """生成 JWT Token"""
    from datetime import datetime, timedelta, timezone
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """解码 JWT Token，返回 payload"""
    if token in _token_blacklist:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

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

async def require_staff(user_id: int, db) -> "User":
    """查询用户并校验 role == 'staff'，非 staff 抛出 HTTPException 403"""
    from sqlalchemy.future import select
    from models import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.role != "staff":
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可操作")
    return user
