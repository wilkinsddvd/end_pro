from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models import QuickReply
from schemas import QuickReplyCreate, QuickReplyOut, QuickReplyListOut
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/quick-replies")
async def list_quick_replies(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        category: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取快速回复列表
    
    参数:
    - page: 页码，默认1
    - size: 每页数量，默认10
    - search: 搜索关键词（标题或内容）
    - category: 分类筛选
    """
    try:
        # 构造动态筛选条件
        stmt = select(QuickReply)
        
        if search:
            stmt = stmt.where(
                QuickReply.title.contains(search) | 
                QuickReply.content.contains(search)
            )
        if category:
            stmt = stmt.where(QuickReply.category == category)
        
        # 按创建时间倒序排列
        stmt = stmt.order_by(QuickReply.created_at.desc())
        
        # 计算总数（使用独立的 COUNT 查询以提升性能）
        count_stmt = select(func.count()).select_from(QuickReply)
        if search:
            count_stmt = count_stmt.where(
                QuickReply.title.contains(search) | 
                QuickReply.content.contains(search)
            )
        if category:
            count_stmt = count_stmt.where(QuickReply.category == category)
        
        total_result = await db.execute(count_stmt)
        total_count = total_result.scalar()
        
        # 分页查询
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await db.execute(stmt)
        quick_replies = result.scalars().all()
        
        # 构造返回数据
        quick_reply_list = []
        for qr in quick_replies:
            quick_reply_list.append({
                "id": qr.id,
                "title": qr.title,
                "content": qr.content,
                "category": qr.category or "",
                "use_count": qr.use_count,
                "created_at": qr.created_at.strftime("%Y-%m-%d") if qr.created_at else ""
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {
                "page": page,
                "size": size,
                "total": total_count,
                "quick_replies": quick_reply_list
            },
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.post("/quick-replies")
async def create_quick_reply(
        data: dict = Body(...),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建新快速回复
    
    请求体:
    - title: 快速回复标题（必填）
    - content: 快速回复内容（必填）
    - category: 快速回复分类（可选）
    """
    try:
        # 验证必填字段
        title = data.get("title")
        content = data.get("content")
        
        if not title:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": "title is required"
            })
        
        if not content:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": "content is required"
            })
        
        # 获取可选字段
        category = data.get("category", "")
        
        # 创建新快速回复
        quick_reply = QuickReply(
            title=title,
            content=content,
            category=category,
            use_count=0
        )
        
        db.add(quick_reply)
        await db.commit()
        await db.refresh(quick_reply)
        
        # 返回新建的快速回复详情
        quick_reply_data = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "category": quick_reply.category or "",
            "use_count": quick_reply.use_count,
            "created_at": quick_reply.created_at.strftime("%Y-%m-%d") if quick_reply.created_at else ""
        }
        
        return JSONResponse(content={
            "code": 201,
            "data": quick_reply_data,
            "msg": "quick reply created successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/quick-replies/{id}")
async def get_quick_reply(id: int, db: AsyncSession = Depends(get_async_db)):
    """
    获取单个快速回复详情
    
    参数:
    - id: 快速回复ID
    """
    try:
        stmt = select(QuickReply).where(QuickReply.id == id)
        result = await db.execute(stmt)
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "quick reply not found"
            })
        
        # 构造返回数据
        quick_reply_data = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "category": quick_reply.category or "",
            "use_count": quick_reply.use_count,
            "created_at": quick_reply.created_at.strftime("%Y-%m-%d") if quick_reply.created_at else ""
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": quick_reply_data,
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/quick-replies/{id}")
async def update_quick_reply(
        id: int,
        data: dict = Body(...),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新快速回复信息
    
    参数:
    - id: 快速回复ID
    
    请求体:
    - title: 快速回复标题（可选）
    - content: 快速回复内容（可选）
    - category: 快速回复分类（可选）
    - use_count: 使用次数（可选）
    """
    try:
        # 查询快速回复是否存在
        stmt = select(QuickReply).where(QuickReply.id == id)
        result = await db.execute(stmt)
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "quick reply not found"
            })
        
        # 更新字段
        if "title" in data and data["title"]:
            quick_reply.title = data["title"]
        
        if "content" in data and data["content"]:
            quick_reply.content = data["content"]
        
        if "category" in data:
            quick_reply.category = data["category"]
        
        if "use_count" in data and isinstance(data["use_count"], int) and data["use_count"] >= 0:
            quick_reply.use_count = data["use_count"]
        
        await db.commit()
        await db.refresh(quick_reply)
        
        # 返回更新后的快速回复详情
        quick_reply_data = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "category": quick_reply.category or "",
            "use_count": quick_reply.use_count,
            "created_at": quick_reply.created_at.strftime("%Y-%m-%d") if quick_reply.created_at else ""
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": quick_reply_data,
            "msg": "quick reply updated successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.delete("/quick-replies/{id}")
async def delete_quick_reply(id: int, db: AsyncSession = Depends(get_async_db)):
    """
    删除快速回复
    
    参数:
    - id: 快速回复ID
    """
    try:
        # 查询快速回复是否存在
        stmt = select(QuickReply).where(QuickReply.id == id)
        result = await db.execute(stmt)
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "quick reply not found"
            })
        
        # 删除快速回复
        await db.delete(quick_reply)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "quick reply deleted successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
