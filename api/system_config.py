from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import TicketCategory
from schemas import TicketCategoryCreate, TicketCategoryUpdate
from db import get_async_db
from fastapi.responses import JSONResponse
from api.deps import get_current_user_id, require_staff

router = APIRouter()


def _category_dict(cat: TicketCategory) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "description": cat.description,
        "sort_order": cat.sort_order,
        "is_active": cat.is_active,
        "created_at": cat.created_at.strftime("%Y-%m-%d") if cat.created_at else "",
    }


@router.get("/system/ticket-categories")
async def list_active_categories(db: AsyncSession = Depends(get_async_db)):
    """获取启用的工单分类列表（无需认证）"""
    try:
        result = await db.execute(
            select(TicketCategory)
            .where(TicketCategory.is_active == 1)
            .order_by(TicketCategory.sort_order, TicketCategory.id)
        )
        categories = result.scalars().all()
        return JSONResponse(content={
            "code": 200,
            "data": {"categories": [_category_dict(c) for c in categories]},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/system/ticket-categories/all")
async def list_all_categories(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取全部工单分类（含禁用，仅 staff）"""
    try:
        await require_staff(user_id, db)
        result = await db.execute(
            select(TicketCategory).order_by(TicketCategory.sort_order, TicketCategory.id)
        )
        categories = result.scalars().all()
        return JSONResponse(content={
            "code": 200,
            "data": {"categories": [_category_dict(c) for c in categories]},
            "msg": "success"
        })
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"code": e.status_code, "data": {}, "msg": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})


@router.post("/system/ticket-categories")
async def create_category(
    data: TicketCategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建工单分类（仅 staff）"""
    try:
        await require_staff(user_id, db)
        existing = (await db.execute(select(TicketCategory).where(TicketCategory.name == data.name))).scalar_one_or_none()
        if existing:
            return JSONResponse(status_code=400, content={"code": 400, "data": {}, "msg": "分类名称已存在"})
        cat = TicketCategory(
            name=data.name,
            description=data.description,
            sort_order=data.sort_order if data.sort_order is not None else 0,
        )
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return JSONResponse(status_code=201, content={"code": 201, "data": _category_dict(cat), "msg": "success"})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"code": e.status_code, "data": {}, "msg": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/system/ticket-categories/{id}")
async def update_category(
    id: int,
    data: TicketCategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新工单分类（仅 staff）"""
    try:
        await require_staff(user_id, db)
        cat = (await db.execute(select(TicketCategory).where(TicketCategory.id == id))).scalar_one_or_none()
        if not cat:
            return JSONResponse(status_code=404, content={"code": 404, "data": {}, "msg": "分类不存在"})
        if data.name is not None and data.name != cat.name:
            existing = (await db.execute(select(TicketCategory).where(TicketCategory.name == data.name))).scalar_one_or_none()
            if existing:
                return JSONResponse(status_code=400, content={"code": 400, "data": {}, "msg": "分类名称已存在"})
            cat.name = data.name
        if data.description is not None:
            cat.description = data.description
        if data.sort_order is not None:
            cat.sort_order = data.sort_order
        if data.is_active is not None:
            cat.is_active = data.is_active
        await db.commit()
        await db.refresh(cat)
        return JSONResponse(content={"code": 200, "data": _category_dict(cat), "msg": "success"})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"code": e.status_code, "data": {}, "msg": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})


@router.delete("/system/ticket-categories/{id}")
async def delete_category(
    id: int,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除工单分类（仅 staff）"""
    try:
        await require_staff(user_id, db)
        cat = (await db.execute(select(TicketCategory).where(TicketCategory.id == id))).scalar_one_or_none()
        if not cat:
            return JSONResponse(status_code=404, content={"code": 404, "data": {}, "msg": "分类不存在"})
        await db.delete(cat)
        await db.commit()
        return JSONResponse(content={"code": 200, "data": {}, "msg": "success"})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"code": e.status_code, "data": {}, "msg": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})
