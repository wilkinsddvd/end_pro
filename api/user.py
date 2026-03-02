import os
import re
import time

from fastapi import APIRouter, Depends, Body, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import get_async_db
from models import User
from api.deps import get_current_user_id
from api.auth import verify_pwd, hash_pwd

router = APIRouter()


def _format_user(user: User) -> dict:
    """Format a User ORM object into the standard API response data structure."""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "bio": user.bio,
        "createdAt": str(user.created_at) if user.created_at else None,
        "preferences": {
            "theme": user.theme or "light",
            "language": user.language or "zh-CN",
            "emailNotification": bool(user.email_notification),
            "smsNotification": bool(user.sms_notification),
            "systemNotification": bool(user.system_notification),
        },
        "privacy": {
            "profilePublic": bool(user.profile_public),
            "showEmail": bool(user.show_email),
            "showPhone": bool(user.show_phone),
            "allowSearch": bool(user.allow_search),
        },
    }


@router.get("/user/info")
async def get_user_info(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})
        return JSONResponse(content={"code": 200, "data": _format_user(user), "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/user/info")
async def update_user_info(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})

        if "nickname" in data:
            nickname = data["nickname"]
            if not isinstance(nickname, str) or not (2 <= len(nickname) <= 20):
                return JSONResponse(content={"code": 400, "data": {}, "msg": "昵称长度应在 2-20 字符之间"})
            user.nickname = nickname

        if "email" in data:
            email = data["email"]
            if not isinstance(email, str) or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                return JSONResponse(content={"code": 400, "data": {}, "msg": "邮箱格式不正确"})
            user.email = email

        if "phone" in data:
            phone = data["phone"]
            if not isinstance(phone, str) or not re.match(r'^1[3-9]\d{9}$', phone):
                return JSONResponse(content={"code": 400, "data": {}, "msg": "手机号格式不正确"})
            user.phone = phone

        if "bio" in data:
            bio = data["bio"]
            if not isinstance(bio, str) or len(bio) > 200:
                return JSONResponse(content={"code": 400, "data": {}, "msg": "个人简介最多 200 字符"})
            user.bio = bio

        await db.commit()
        await db.refresh(user)
        return JSONResponse(content={"code": 200, "data": _format_user(user), "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/user/password")
async def update_password(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        old_password = data.get("oldPassword", "")
        new_password = data.get("newPassword", "")
        confirm_password = data.get("confirmPassword", "")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})

        if not verify_pwd(old_password, user.password_hash):
            return JSONResponse(content={"code": 400, "data": {}, "msg": "原密码不正确"})

        if new_password != confirm_password:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "两次输入的新密码不一致"})

        if len(new_password) < 8:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "新密码长度至少 8 位"})

        if not (re.search(r'[A-Za-z]', new_password) and re.search(r'[0-9]', new_password)):
            return JSONResponse(content={"code": 400, "data": {}, "msg": "新密码需同时包含字母和数字"})

        if verify_pwd(new_password, user.password_hash):
            return JSONResponse(content={"code": 400, "data": {}, "msg": "新密码不能与旧密码相同"})

        user.password_hash = hash_pwd(new_password)
        await db.commit()
        return JSONResponse(content={"code": 200, "data": {}, "msg": "密码修改成功"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.post("/user/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        if file.content_type not in ("image/jpeg", "image/png"):
            return JSONResponse(content={"code": 400, "data": {}, "msg": "仅支持 JPEG 或 PNG 格式"})

        content = await file.read()
        if len(content) > 2 * 1024 * 1024:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "文件大小不能超过 2MB"})

        ext = "jpg" if file.content_type == "image/jpeg" else "png"
        filename = f"{user_id}_{int(time.time())}.{ext}"
        save_dir = "static/avatars"
        save_path = os.path.join(save_dir, filename)

        with open(save_path, "wb") as f:
            f.write(content)

        avatar_url = f"/static/avatars/{filename}"
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if user:
            user.avatar = avatar_url
            await db.commit()

        return JSONResponse(content={"code": 200, "data": {"avatar_url": avatar_url}, "msg": "头像上传成功"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/user/preferences")
async def update_preferences(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})

        if "theme" in data:
            if data["theme"] not in ("light", "dark", "auto"):
                return JSONResponse(content={"code": 400, "data": {}, "msg": "theme 只允许 light/dark/auto"})
            user.theme = data["theme"]

        if "language" in data:
            if data["language"] not in ("zh-CN", "en-US"):
                return JSONResponse(content={"code": 400, "data": {}, "msg": "language 只允许 zh-CN/en-US"})
            user.language = data["language"]

        if "emailNotification" in data:
            user.email_notification = 1 if data["emailNotification"] else 0

        if "smsNotification" in data:
            user.sms_notification = 1 if data["smsNotification"] else 0

        if "systemNotification" in data:
            user.system_notification = 1 if data["systemNotification"] else 0

        await db.commit()
        await db.refresh(user)
        return JSONResponse(content={
            "code": 200,
            "data": _format_user(user)["preferences"],
            "msg": "success",
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/user/privacy")
async def update_privacy(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "user not found"})

        if "profilePublic" in data:
            user.profile_public = 1 if data["profilePublic"] else 0

        if "showEmail" in data:
            user.show_email = 1 if data["showEmail"] else 0

        if "showPhone" in data:
            user.show_phone = 1 if data["showPhone"] else 0

        if "allowSearch" in data:
            user.allow_search = 1 if data["allowSearch"] else 0

        await db.commit()
        await db.refresh(user)
        return JSONResponse(content={
            "code": 200,
            "data": _format_user(user)["privacy"],
            "msg": "success",
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
