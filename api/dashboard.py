from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from models import Ticket
from db import get_async_db
from fastapi.responses import JSONResponse
import datetime

router = APIRouter(prefix="/dashboard")


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(
            func.count(Ticket.id).label("total"),
            func.sum(case((Ticket.status == "open", 1), else_=0)).label("new_tickets"),
            func.sum(case((Ticket.status.in_(["resolved", "closed"]), 1), else_=0)).label("completed")
        )
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
                "avgResponseTime": 0,  # TODO: calculate actual average response time
                "overdueTickets": overdue_count
            },
            "msg": "success"
        })
    except Exception:
        return JSONResponse(content={"code": 500, "data": {}, "msg": "获取仪表盘统计数据失败"})


@router.get("/trend")
async def get_ticket_trend(
        time_range: str = Query("week", alias="range", regex="^(week|month)$"),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        today = datetime.date.today()
        if time_range == "week":
            days = 7
        else:
            days = 30

        start_date = today - datetime.timedelta(days=days - 1)
        dates = [start_date + datetime.timedelta(days=i) for i in range(days)]

        new_stmt = (
            select(Ticket.created_at.label("date"), func.count(Ticket.id).label("count"))
            .where(Ticket.created_at >= start_date)
            .group_by(Ticket.created_at)
        )
        new_result = await db.execute(new_stmt)
        new_map = {row.date: row.count for row in new_result.all()}

        completed_stmt = (
            select(Ticket.updated_at.label("date"), func.count(Ticket.id).label("count"))
            .where(
                Ticket.updated_at >= start_date,
                Ticket.status.in_(["resolved", "closed"])
            )
            .group_by(Ticket.updated_at)
        )
        completed_result = await db.execute(completed_stmt)
        completed_map = {row.date: row.count for row in completed_result.all()}

        return JSONResponse(content={
            "code": 200,
            "data": {
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "newTickets": [new_map.get(d, 0) for d in dates],
                "completedTickets": [completed_map.get(d, 0) for d in dates]
            },
            "msg": "success"
        })
    except Exception:
        return JSONResponse(content={"code": 500, "data": {}, "msg": "获取工单趋势数据失败"})


@router.get("/category-stats")
async def get_category_stats(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = (
            select(Ticket.category, func.count(Ticket.id).label("count"))
            .where(Ticket.category.isnot(None))
            .group_by(Ticket.category)
            .order_by(func.count(Ticket.id).desc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        data = [{"category": row.category, "count": row.count} for row in rows]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception:
        return JSONResponse(content={"code": 500, "data": {}, "msg": "获取工单分类统计失败"})
