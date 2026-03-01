from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from models import Ticket, User
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
import datetime

router = APIRouter(prefix="/statistics")


@router.get("/overview")
async def get_overview(
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    try:
        stmt = select(func.count(Ticket.id).label("total"),
                      func.sum(case((Ticket.status == "open", 1), else_=0)).label("new_tickets"),
                      func.sum(case((Ticket.status.in_(["resolved", "closed"]), 1), else_=0)).label("completed"))
        if startDate:
            stmt = stmt.where(Ticket.created_at >= datetime.date.fromisoformat(startDate))
        if endDate:
            stmt = stmt.where(Ticket.created_at <= datetime.date.fromisoformat(endDate))
        result = await db.execute(stmt)
        row = result.one()
        overdue_stmt = select(func.count(Ticket.id)).where(
            Ticket.due_date.isnot(None),
            Ticket.due_date < datetime.date.today(),
            Ticket.status.notin_(["resolved", "closed"])
        )
        overdue_result = await db.execute(overdue_stmt)
        overdue_count = overdue_result.scalar() or 0
        return JSONResponse(content={
            "code": 200,
            "data": {
                "totalTickets": row.total or 0,
                "newTickets": int(row.new_tickets or 0),
                "completedTickets": int(row.completed or 0),
                "avgResponseTime": 0,
                "overdueTickets": overdue_count
            },
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/status-distribution")
async def get_status_distribution(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Ticket.status, func.count(Ticket.id).label("count")).group_by(Ticket.status)
        result = await db.execute(stmt)
        rows = result.all()
        data = [{"status": row.status, "count": row.count} for row in rows]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/priority-distribution")
async def get_priority_distribution(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Ticket.priority, func.count(Ticket.id).label("count")).group_by(Ticket.priority)
        result = await db.execute(stmt)
        rows = result.all()
        data = [{"priority": row.priority, "count": row.count} for row in rows]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/user-handling")
async def get_user_handling(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = (
            select(
                User.username,
                func.sum(case((Ticket.status == "open", 1), else_=0)).label("new_tickets"),
                func.sum(case((Ticket.status.in_(["resolved", "closed"]), 1), else_=0)).label("completed_tickets")
            )
            .join(User, Ticket.user_id == User.id)
            .group_by(User.id, User.username)
        )
        result = await db.execute(stmt)
        rows = result.all()
        data = [
            {
                "username": row.username,
                "newTickets": int(row.new_tickets or 0),
                "completedTickets": int(row.completed_tickets or 0)
            }
            for row in rows
        ]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/response-time")
async def get_response_time(
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    try:
        stmt = select(Ticket.created_at.label("date"), func.count(Ticket.id).label("count")).group_by(Ticket.created_at).order_by(Ticket.created_at)
        if startDate:
            stmt = stmt.where(Ticket.created_at >= datetime.date.fromisoformat(startDate))
        if endDate:
            stmt = stmt.where(Ticket.created_at <= datetime.date.fromisoformat(endDate))
        result = await db.execute(stmt)
        rows = result.all()
        data = [
            {
                "date": row.date.strftime("%Y-%m-%d") if row.date else "",
                "avgResponseTime": 0,
                "maxResponseTime": 0
            }
            for row in rows
        ]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
