from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from models import Ticket
from db import get_async_db
from api.deps import get_current_user_id
from fastapi.responses import JSONResponse
import datetime

router = APIRouter(prefix="/dashboard")

CATEGORY_MAP = {
    "technical": "技术支持",
    "after_sales": "售后服务",
    "product": "产品咨询",
}


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        today = datetime.date.today()
        stmt = select(
            func.sum(case((Ticket.status == "open", 1), else_=0)).label("new_tickets"),
            func.sum(case((Ticket.status == "in_progress", 1), else_=0)).label("processing_tickets"),
            func.sum(case((Ticket.status.in_(["resolved", "closed"]), 1), else_=0)).label("completed_tickets"),
        )
        result = await db.execute(stmt)
        row = result.one()

        overdue_stmt = select(func.count(Ticket.id)).where(
            Ticket.due_date.isnot(None),
            Ticket.due_date < today,
            Ticket.status.notin_(["resolved", "closed"]),
        )
        overdue_result = await db.execute(overdue_stmt)
        overdue_count = overdue_result.scalar() or 0

        return JSONResponse(content={
            "code": 200,
            "data": {
                "newTickets": int(row.new_tickets or 0),
                "newTicketsTrend": 0,
                "processingTickets": int(row.processing_tickets or 0),
                "processingTicketsTrend": 0,
                "completedTickets": int(row.completed_tickets or 0),
                "completedTicketsTrend": 0,
                "overdueTickets": int(overdue_count),
                "overdueTrend": 0,
            },
            "msg": "success",
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/trend")
async def get_trend(
    range: str = Query(default="week"),
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        today = datetime.date.today()
        days = 30 if range == "month" else 7
        start_date = today - datetime.timedelta(days=days - 1)

        stmt = select(
            Ticket.created_at.label("date"),
            func.sum(case((Ticket.status == "open", 1), else_=0)).label("new_tickets"),
            func.sum(case((Ticket.status.in_(["resolved", "closed"]), 1), else_=0)).label("completed_tickets"),
        ).where(
            Ticket.created_at >= start_date,
            Ticket.created_at <= today,
        ).group_by(Ticket.created_at).order_by(Ticket.created_at)

        result = await db.execute(stmt)
        rows = result.all()

        row_map = {row.date: row for row in rows}
        dates = []
        new_tickets = []
        completed_tickets = []
        for i in range(days):
            d = start_date + datetime.timedelta(days=i)
            dates.append(d.strftime("%m/%d"))
            row = row_map.get(d)
            new_tickets.append(int(row.new_tickets or 0) if row else 0)
            completed_tickets.append(int(row.completed_tickets or 0) if row else 0)

        return JSONResponse(content={
            "code": 200,
            "data": {
                "dates": dates,
                "newTickets": new_tickets,
                "completedTickets": completed_tickets,
            },
            "msg": "success",
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.get("/category-stats")
async def get_category_stats(
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        stmt = select(
            Ticket.category,
            func.count(Ticket.id).label("count"),
        ).group_by(Ticket.category)

        result = await db.execute(stmt)
        rows = result.all()

        data = [
            {
                "name": CATEGORY_MAP.get(row.category, "其他"),
                "value": row.count,
            }
            for row in rows
        ]

        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
