from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Ticket, User, TicketHistory
from schemas import TicketCreate, TicketOut
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from api.deps import get_current_user_id
import datetime

router = APIRouter()

# 常量定义
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
VALID_STATUSES = ["open", "in_progress", "resolved", "closed"]

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
        stmt = select(Ticket).options(selectinload(Ticket.user), selectinload(Ticket.assignee))
        
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
        
        # 计算总数（使用独立的 COUNT 查询以提升性能）
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(Ticket)
        if search:
            count_stmt = count_stmt.where(
                Ticket.title.contains(search) | 
                Ticket.description.contains(search)
            )
        if status:
            count_stmt = count_stmt.where(Ticket.status == status)
        if category:
            count_stmt = count_stmt.where(Ticket.category == category)
        if priority:
            count_stmt = count_stmt.where(Ticket.priority == priority)
        
        total_result = await db.execute(count_stmt)
        total_count = total_result.scalar()
        
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
                "updated_at": ticket.updated_at.strftime("%Y-%m-%d") if ticket.updated_at else "",
                "user": ticket.user.username if ticket.user else None,
                "due_date": ticket.due_date.strftime("%Y-%m-%d") if ticket.due_date else None,
                "assignee_id": ticket.assignee_id,
                "assignee": ticket.assignee.username if ticket.assignee else None,
                "is_overdue": (
                    ticket.due_date is not None
                    and ticket.status not in ("resolved", "closed")
                    and ticket.due_date < datetime.date.today()
                ),
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
        db: AsyncSession = Depends(get_async_db),
        user_id: int = Depends(get_current_user_id)
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
        due_date_str = data.get("due_date")
        assignee_id = data.get("assignee_id")
        
        # 验证优先级值
        if priority not in VALID_PRIORITIES:
            priority = "medium"
        
        # 解析截止日期
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.date.fromisoformat(due_date_str)
            except ValueError:
                pass
        
        # 创建新工单
        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            status="open",  # 新建工单默认为 open 状态
            user_id=user_id,   # 来自 JWT
            due_date=due_date,
            assignee_id=assignee_id
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        # 加载用户信息
        stmt = select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.user), selectinload(Ticket.assignee))
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
            "updated_at": ticket.updated_at.strftime("%Y-%m-%d") if ticket.updated_at else "",
            "user": ticket.user.username if ticket.user else None,
            "due_date": ticket.due_date.strftime("%Y-%m-%d") if ticket.due_date else None,
            "assignee_id": ticket.assignee_id,
            "assignee": ticket.assignee.username if ticket.assignee else None,
            "is_overdue": (
                ticket.due_date is not None
                and ticket.status not in ("resolved", "closed")
                and ticket.due_date < datetime.date.today()
            ),
        }
        
        return JSONResponse(content={
            "code": 201,
            "data": ticket_data,
            "msg": "ticket created successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/tickets/{id}")
async def get_ticket(id: int, db: AsyncSession = Depends(get_async_db)):
    """
    获取单个工单详情
    
    参数:
    - id: 工单ID
    """
    try:
        # 使用 selectinload 预加载用户信息，防止 missing greenlet 问题
        stmt = (
            select(Ticket)
            .where(Ticket.id == id)
            .options(selectinload(Ticket.user), selectinload(Ticket.assignee))
        )
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "ticket not found"
            })
        
        # 构造返回数据
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description or "",
            "category": ticket.category or "",
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "",
            "updated_at": ticket.updated_at.strftime("%Y-%m-%d") if ticket.updated_at else "",
            "user": ticket.user.username if ticket.user else None,
            "due_date": ticket.due_date.strftime("%Y-%m-%d") if ticket.due_date else None,
            "assignee_id": ticket.assignee_id,
            "assignee": ticket.assignee.username if ticket.assignee else None,
            "is_overdue": (
                ticket.due_date is not None
                and ticket.status not in ("resolved", "closed")
                and ticket.due_date < datetime.date.today()
            ),
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": ticket_data,
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.put("/tickets/{id}")
async def update_ticket(
        id: int,
        data: dict = Body(...),
        db: AsyncSession = Depends(get_async_db),
        user_id: int = Depends(get_current_user_id)
):
    """
    更新工单状态

    参数:
    - id: 工单ID

    请求体:
    - status: 新状态（必填，仅允许变更状态）
    """
    try:
        # 查询工单是否存在
        stmt = select(Ticket).where(Ticket.id == id)
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "ticket not found"
            })

        new_status = data.get("status")
        if not new_status or new_status not in VALID_STATUSES:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": "invalid or missing status"
            })

        if new_status == ticket.status:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": "status has not changed"
            })

        old_status = ticket.status
        ticket.status = new_status
        ticket.updated_at = datetime.date.today()

        # 当工单状态变为 resolved 或 closed 时，自动设置 completed_at
        if new_status in ("resolved", "closed") and ticket.completed_at is None:
            ticket.completed_at = datetime.datetime.now()

        # 查操作人用户名
        user_result = await db.execute(select(User).where(User.id == user_id))
        operator_user = user_result.scalar_one_or_none()
        operator_name = operator_user.username if operator_user else None

        # 写历史
        history = TicketHistory(
            ticket_id=ticket.id,
            old_status=old_status,
            new_status=new_status,
            operator=operator_name,
            changed_at=datetime.date.today()
        )
        db.add(history)
        await db.commit()
        await db.refresh(ticket)

        # 加载用户信息
        stmt = select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.user), selectinload(Ticket.assignee))
        result = await db.execute(stmt)
        ticket = result.scalar_one()

        # 返回更新后的工单详情
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description or "",
            "category": ticket.category or "",
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "",
            "updated_at": ticket.updated_at.strftime("%Y-%m-%d") if ticket.updated_at else "",
            "user": ticket.user.username if ticket.user else None,
            "due_date": ticket.due_date.strftime("%Y-%m-%d") if ticket.due_date else None,
            "assignee_id": ticket.assignee_id,
            "assignee": ticket.assignee.username if ticket.assignee else None,
            "is_overdue": (
                ticket.due_date is not None
                and ticket.status not in ("resolved", "closed")
                and ticket.due_date < datetime.date.today()
            ),
        }

        return JSONResponse(content={
            "code": 200,
            "data": ticket_data,
            "msg": "ticket updated successfully"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/tickets/{id}/history")
async def get_ticket_history(id: int, db: AsyncSession = Depends(get_async_db)):
    """
    获取工单状态变更历史列表
    - 按 changed_at 升序返回所有历史记录
    """
    try:
        # 验证工单存在
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == id))
        if not ticket_result.scalar_one_or_none():
            return JSONResponse(content={
                "code": 404,
                "data": {},
                "msg": "ticket not found"
            })

        stmt = (
            select(TicketHistory)
            .where(TicketHistory.ticket_id == id)
            .order_by(TicketHistory.changed_at.asc(), TicketHistory.id.asc())
        )
        result = await db.execute(stmt)
        histories = result.scalars().all()

        return JSONResponse(content={
            "code": 200,
            "data": {
                "history": [
                    {
                        "id": h.id,
                        "ticket_id": h.ticket_id,
                        "old_status": h.old_status,
                        "new_status": h.new_status,
                        "operator": h.operator,
                        "changed_at": h.changed_at.strftime("%Y-%m-%d") if h.changed_at else ""
                    }
                    for h in histories
                ],
                "total": len(histories)
            },
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
