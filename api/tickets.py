from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models import Ticket, TicketHistory, User
from schemas import TicketCreate, TicketUpdate, TicketOut, VALID_PRIORITIES, VALID_STATUSES, TICKET_TRANSITIONS
from db import get_async_db
from auth_utils import get_current_user
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload

router = APIRouter()


def _ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description or "",
        "category": ticket.category or "",
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "",
        "user": ticket.user.username if ticket.user else None,
    }


@router.get("/tickets")
async def list_tickets(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取工单列表 - 只返回当前登录用户创建的工单

    Filters: search (title/description), status, category, priority
    """
    stmt = select(Ticket).where(Ticket.user_id == current_user.id).options(selectinload(Ticket.user))
    count_stmt = select(func.count()).select_from(Ticket).where(Ticket.user_id == current_user.id)

    if search:
        cond = Ticket.title.contains(search) | Ticket.description.contains(search)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if status:
        stmt = stmt.where(Ticket.status == status)
        count_stmt = count_stmt.where(Ticket.status == status)
    if category:
        stmt = stmt.where(Ticket.category == category)
        count_stmt = count_stmt.where(Ticket.category == category)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
        count_stmt = count_stmt.where(Ticket.priority == priority)

    total_count = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size)
    tickets = (await db.execute(stmt)).scalars().all()

    return JSONResponse(content={
        "code": 200,
        "data": {
            "page": page,
            "size": size,
            "total": total_count,
            "tickets": [_ticket_to_dict(t) for t in tickets],
        },
        "msg": "success"
    })


@router.post("/tickets")
async def create_ticket(
        data: TicketCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """创建新工单 - Requires auth. Sets status=open and records initial history."""
    ticket = Ticket(
        title=data.title,
        description=data.description or "",
        category=data.category or "",
        priority=data.priority,
        status="open",
        user_id=current_user.id,
    )
    db.add(ticket)
    await db.flush()  # get ticket.id without committing

    # Record initial history entry
    history = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=current_user.id,
        old_status=None,
        new_status="open",
        note="ticket created",
    )
    db.add(history)
    await db.commit()
    await db.refresh(ticket)

    stmt = select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.user))
    ticket = (await db.execute(stmt)).scalar_one()

    return JSONResponse(content={
        "code": 201,
        "data": _ticket_to_dict(ticket),
        "msg": "ticket created successfully"
    })


@router.get("/tickets/{id}")
async def get_ticket(
        id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """获取单个工单详情 - 只允许查看自己的工单"""
    stmt = (
        select(Ticket)
        .where(Ticket.id == id, Ticket.user_id == current_user.id)
        .options(selectinload(Ticket.user))
    )
    ticket = (await db.execute(stmt)).scalar_one_or_none()
    if not ticket:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "ticket not found"})
    return JSONResponse(content={"code": 200, "data": _ticket_to_dict(ticket), "msg": "success"})


@router.put("/tickets/{id}")
async def update_ticket(
        id: int,
        data: TicketUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """
    更新工单信息 - 只允许更新自己的工单

    Status transitions are validated against allowed rules:
    open -> in_progress | closed
    in_progress -> resolved | open | closed
    resolved -> closed | open
    closed -> (no further transitions)
    """
    stmt = select(Ticket).where(Ticket.id == id, Ticket.user_id == current_user.id)
    ticket = (await db.execute(stmt)).scalar_one_or_none()
    if not ticket:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "ticket not found"})

    if data.title:
        ticket.title = data.title
    if data.description is not None:
        ticket.description = data.description
    if data.category is not None:
        ticket.category = data.category
    if data.priority and data.priority in VALID_PRIORITIES:
        ticket.priority = data.priority

    # Status transition with validation and history recording
    if data.status is not None:
        new_status = data.status
        if new_status not in VALID_STATUSES:
            return JSONResponse(content={
                "code": 400,
                "data": {},
                "msg": f"invalid status '{new_status}', allowed: {VALID_STATUSES}"
            })
        allowed = TICKET_TRANSITIONS.get(ticket.status, [])
        if new_status != ticket.status and new_status not in allowed:
            return JSONResponse(content={
                "code": 422,
                "data": {},
                "msg": f"transition from '{ticket.status}' to '{new_status}' is not allowed"
            })
        if new_status != ticket.status:
            history = TicketHistory(
                ticket_id=ticket.id,
                changed_by_id=current_user.id,
                old_status=ticket.status,
                new_status=new_status,
                note=data.note or "",
            )
            db.add(history)
            ticket.status = new_status

    await db.commit()
    await db.refresh(ticket)

    stmt = select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.user))
    ticket = (await db.execute(stmt)).scalar_one()
    return JSONResponse(content={
        "code": 200,
        "data": _ticket_to_dict(ticket),
        "msg": "ticket updated successfully"
    })


@router.delete("/tickets/{id}")
async def delete_ticket(
        id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """删除工单 - 只允许删除自己的工单"""
    stmt = select(Ticket).where(Ticket.id == id, Ticket.user_id == current_user.id)
    ticket = (await db.execute(stmt)).scalar_one_or_none()
    if not ticket:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "ticket not found"})
    await db.delete(ticket)
    await db.commit()
    return JSONResponse(content={"code": 200, "data": {}, "msg": "ticket deleted successfully"})


@router.get("/tickets/{id}/history")
async def get_ticket_history(
        id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取工单状态变更历史记录 - 只允许查看自己工单的历史

    Returns a list of status change records for the given ticket.
    """
    # Verify ticket ownership
    stmt = select(Ticket).where(Ticket.id == id, Ticket.user_id == current_user.id)
    ticket = (await db.execute(stmt)).scalar_one_or_none()
    if not ticket:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "ticket not found"})

    hist_stmt = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == id)
        .options(selectinload(TicketHistory.changed_by))
        .order_by(TicketHistory.changed_at.asc())
    )
    history_records = (await db.execute(hist_stmt)).scalars().all()

    history_list = [
        {
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "note": h.note or "",
            "changed_by": h.changed_by.username if h.changed_by else "",
            "changed_at": h.changed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if h.changed_at else "",
        }
        for h in history_records
    ]

    return JSONResponse(content={
        "code": 200,
        "data": {"ticket_id": id, "history": history_list},
        "msg": "success"
    })
