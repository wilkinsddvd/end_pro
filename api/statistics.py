from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from models import Ticket, User
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
import datetime
import statistics as stats_lib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics")


def _calc_response_hours(created_at, first_response_at):
    """计算响应时长（小时），created_at 可为 date 或 datetime"""
    if first_response_at is None:
        return None
    if isinstance(created_at, datetime.date) and not isinstance(created_at, datetime.datetime):
        created_dt = datetime.datetime.combine(created_at, datetime.time.min)
    else:
        created_dt = created_at
    delta = first_response_at - created_dt
    return delta.total_seconds() / 3600.0


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

        # 计算响应时长统计
        rt_stmt = select(Ticket.created_at, Ticket.first_response_at).where(
            Ticket.first_response_at.isnot(None)
        )
        if startDate:
            rt_stmt = rt_stmt.where(Ticket.created_at >= datetime.date.fromisoformat(startDate))
        if endDate:
            rt_stmt = rt_stmt.where(Ticket.created_at <= datetime.date.fromisoformat(endDate))
        rt_result = await db.execute(rt_stmt)
        rt_rows = rt_result.all()
        response_times = [
            _calc_response_hours(r.created_at, r.first_response_at)
            for r in rt_rows
            if _calc_response_hours(r.created_at, r.first_response_at) is not None
        ]

        total_tickets = int(row.total or 0)
        responded_count = len(response_times)
        avg_rt = round(sum(response_times) / responded_count, 2) if responded_count > 0 else 0
        median_rt = round(stats_lib.median(response_times), 2) if responded_count > 0 else 0
        respond_rate = round(responded_count / total_tickets * 100, 1) if total_tickets > 0 else 0

        return JSONResponse(content={
            "code": 200,
            "data": {
                "totalTickets": total_tickets,
                "newTickets": int(row.new_tickets or 0),
                "completedTickets": int(row.completed or 0),
                "overdueTickets": overdue_count,
                "avgResponseTime": avg_rt,
                "medianResponseTime": median_rt,
                "respondRate": respond_rate
            },
            "msg": "success"
        })
    except Exception as e:
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})


@router.get("/status-distribution")
async def get_status_distribution(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Ticket.status, func.count(Ticket.id).label("count")).group_by(Ticket.status)
        result = await db.execute(stmt)
        rows = result.all()
        data = [{"status": row.status, "count": row.count} for row in rows]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})


@router.get("/priority-distribution")
async def get_priority_distribution(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Ticket.priority, func.count(Ticket.id).label("count")).group_by(Ticket.priority)
        result = await db.execute(stmt)
        rows = result.all()
        data = [{"priority": row.priority, "count": row.count} for row in rows]
        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})


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
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})


@router.get("/response-time")
async def get_response_time(
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db)
):
    try:
        stmt = select(Ticket.created_at, Ticket.first_response_at)
        if startDate:
            stmt = stmt.where(Ticket.created_at >= datetime.date.fromisoformat(startDate))
        if endDate:
            stmt = stmt.where(Ticket.created_at <= datetime.date.fromisoformat(endDate))
        stmt = stmt.order_by(Ticket.created_at)
        result = await db.execute(stmt)
        rows = result.all()

        # 按日期分组计算统计数据
        date_map = {}
        for row in rows:
            date_key = row.created_at.strftime("%Y-%m-%d") if row.created_at else ""
            if date_key not in date_map:
                date_map[date_key] = {"times": [], "total": 0}
            date_map[date_key]["total"] += 1
            if row.first_response_at is not None:
                hours = _calc_response_hours(row.created_at, row.first_response_at)
                if hours is not None and hours >= 0:
                    date_map[date_key]["times"].append(hours)

        data = []
        for date_key in sorted(date_map.keys()):
            entry = date_map[date_key]
            times = entry["times"]
            responded = len(times)
            data.append({
                "date": date_key,
                "avgResponseTime": round(sum(times) / responded, 2) if responded > 0 else 0,
                "maxResponseTime": round(max(times), 2) if responded > 0 else 0,
                "minResponseTime": round(min(times), 2) if responded > 0 else 0,
                "totalTickets": entry["total"],
                "respondedTickets": responded,
            })

        return JSONResponse(content={"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})


@router.get("/avg-response-time")
async def get_avg_response_time(db: AsyncSession = Depends(get_async_db)):
    try:
        stmt = select(Ticket.created_at, Ticket.first_response_at)
        result = await db.execute(stmt)
        rows = result.all()

        total_tickets = len(rows)
        response_times = []
        for row in rows:
            if row.first_response_at is not None:
                hours = _calc_response_hours(row.created_at, row.first_response_at)
                if hours is not None and hours >= 0:
                    response_times.append(hours)

        responded_count = len(response_times)
        avg_rt = round(sum(response_times) / responded_count, 2) if responded_count > 0 else 0
        max_rt = round(max(response_times), 2) if responded_count > 0 else 0
        min_rt = round(min(response_times), 2) if responded_count > 0 else 0
        median_rt = round(stats_lib.median(response_times), 2) if responded_count > 0 else 0
        respond_rate = round(responded_count / total_tickets * 100, 1) if total_tickets > 0 else 0

        return JSONResponse(content={
            "code": 200,
            "data": {
                "avgResponseTime": avg_rt,
                "maxResponseTime": max_rt,
                "minResponseTime": min_rt,
                "medianResponseTime": median_rt,
                "respondRate": respond_rate
            },
            "msg": "success"
        })
    except Exception as e:
        logger.exception("Statistics error: %s", e)
        return JSONResponse(content={"code": 500, "data": {}, "msg": "内部错误，请稍后重试"})
