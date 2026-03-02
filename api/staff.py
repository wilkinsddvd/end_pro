import re
from typing import Optional

from fastapi import APIRouter, Depends, Body, Query
from fastapi.responses import JSONResponse
from sqlalchemy import or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_async_db
from models import User
from api.deps import get_current_user_id
from api.auth import hash_pwd

router = APIRouter()


@router.get("/staff/list")
async def get_staff_list(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取所有后勤人员（不分页，用于下拉框）"""
    result = await db.execute(select(User).where(User.role == "staff"))
    staff = result.scalars().all()
    return JSONResponse(content={
        "code": 200,
        "data": {"staff": [{"id": u.id, "username": u.username, "nickname": u.nickname} for u in staff]},
        "msg": "success"
    })


@router.get("/staff")
async def list_staff(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取后勤人员列表（分页+搜索）"""
    count_query = select(func.count()).select_from(User).where(User.role == "staff")
    if search:
        count_query = count_query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.nickname.ilike(f"%{search}%")
            )
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    paged_query = select(User).where(User.role == "staff")
    if search:
        paged_query = paged_query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.nickname.ilike(f"%{search}%")
            )
        )
    paged_query = paged_query.offset((page - 1) * size).limit(size)
    result = await db.execute(paged_query)
    staff = result.scalars().all()

    return JSONResponse(content={
        "code": 200,
        "data": {
            "page": page,
            "size": size,
            "total": total,
            "staff": [
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "phone": u.phone,
                    "created_at": str(u.created_at) if u.created_at else None
                }
                for u in staff
            ]
        },
        "msg": "success"
    })


@router.post("/staff")
async def create_staff(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """新增后勤人员"""
    username = data.get("username", "").strip()
    password = data.get("password", "")
    nickname = data.get("nickname", None)
    phone = data.get("phone", None)

    if not username or not (3 <= len(username) <= 32):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username must be 3-32 characters"})
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "username may only contain letters, digits and underscores"})
    if not password or len(password) < 8:
        return JSONResponse(content={"code": 400, "data": {}, "msg": "password must be at least 8 characters"})
    if not (re.search(r'[A-Za-z]', password) and re.search(r'[0-9]', password)):
        return JSONResponse(content={"code": 400, "data": {}, "msg": "password must contain both letters and digits"})

    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar():
        return JSONResponse(content={"code": 409, "data": {}, "msg": "username is already taken"})

    user = User(
        username=username,
        password_hash=hash_pwd(password),
        nickname=nickname,
        phone=phone,
        role="staff"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return JSONResponse(status_code=201, content={
        "code": 201,
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "phone": user.phone,
            "created_at": str(user.created_at) if user.created_at else None
        },
        "msg": "success"
    })


@router.put("/staff/{id}")
async def update_staff(
    id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新后勤人员信息"""
    result = await db.execute(select(User).where(User.id == id))
    staff = result.scalar()
    if not staff or staff.role != "staff":
        return JSONResponse(content={"code": 404, "data": {}, "msg": "staff not found"})

    if "nickname" in data:
        staff.nickname = data["nickname"]
    if "phone" in data:
        staff.phone = data["phone"]

    await db.commit()
    await db.refresh(staff)

    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": staff.id,
            "username": staff.username,
            "nickname": staff.nickname,
            "phone": staff.phone,
            "created_at": str(staff.created_at) if staff.created_at else None
        },
        "msg": "success"
    })


@router.delete("/staff/{id}")
async def delete_staff(
    id: int,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除后勤人员（软删除：将 role 改为 user）"""
    result = await db.execute(select(User).where(User.id == id))
    staff = result.scalar()
    if not staff or staff.role != "staff":
        return JSONResponse(content={"code": 404, "data": {}, "msg": "staff not found"})

    staff.role = "user"
    await db.commit()

    return JSONResponse(content={"code": 200, "data": {}, "msg": "staff removed successfully"})
