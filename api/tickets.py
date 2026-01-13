from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Ticket, User
from schemas import TicketCreate, TicketOut
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/tickets")
async def list_tickets(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取工单列表
    
    参数:
    - page: 页码，默认1
    - size: 每页数量，默认10
    - search: 搜索关键词（标题或描述）
    - status: 状态筛选（open, in_progress, resolved, closed）
    - category: 分类筛选
    - priority: 优先级筛选（low, medium, high, urgent）
    """
    try:
        # 构造动态筛选条件
        stmt = select(Ticket).options(selectinload(Ticket.user))
        
        if search:
            stmt = stmt.where(
                Ticket.title.contains(search) | 
                Ticket.description.contains(search)
            )
        if status:
            stmt = stmt.where(Ticket.status == status)
        if category:
            stmt = stmt.where(Ticket.category == category)
        if priority:
            stmt = stmt.where(Ticket.priority == priority)
        
        # 按创建时间倒序排列
        stmt = stmt.order_by(Ticket.created_at.desc())
        
        # 计算总数
        total_result = await db.execute(stmt)
        total_count = len(total_result.scalars().all())
        
        # 分页查询
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await db.execute(stmt)
        tickets = result.scalars().all()
        
        # 构造返回数据
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                "id": ticket.id,
                "title": ticket.title,
                "description": ticket.description or "",
                "category": ticket.category or "",
                "priority": ticket.priority,
                "status": ticket.status,
                "created_at": ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "",
                "user": ticket.user.username if ticket.user else None
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {
                "page": page,
                "size": size,
                "total": total_count,
                "tickets": ticket_list
            },
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.post("/tickets")
async def create_ticket(
        data: dict = Body(...),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建新工单
    
    请求体:
    - title: 工单标题（必填）
    - description: 工单描述（可选）
    - category: 工单分类（可选）
    - priority: 优先级（可选，默认medium）
    """
    try:
        # 验证必填字段
        title = data.get("title")
        if not title:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": "title is required"
            })
        
        # 获取可选字段
        description = data.get("description", "")
        category = data.get("category", "")
        priority = data.get("priority", "medium")
        
        # 验证优先级值
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            priority = "medium"
        
        # 创建新工单（简化演示，默认 user_id=1）
        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            status="open",  # 新建工单默认为 open 状态
            user_id=1  # 简化演示，实际应从认证信息获取
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        # 加载用户信息
        stmt = select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.user))
        result = await db.execute(stmt)
        ticket = result.scalar_one()
        
        # 返回新建的工单详情
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description or "",
            "category": ticket.category or "",
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "",
            "user": ticket.user.username if ticket.user else None
        }
        
        return JSONResponse(content={
            "code": 201,
            "data": ticket_data,
            "msg": "ticket created successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
