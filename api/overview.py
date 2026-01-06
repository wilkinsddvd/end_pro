from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract
from models import Ticket, TicketCategory
from db import get_async_db
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/overview/tickets")
async def get_ticket_overview(db: AsyncSession = Depends(get_async_db)):
    """Get ticket overview statistics"""
    try:
        # Total tickets
        total_result = await db.execute(select(func.count(Ticket.id)))
        total = total_result.scalar()
        
        # Open tickets
        open_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "open")
        )
        open_count = open_result.scalar()
        
        # In progress tickets
        in_progress_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "in_progress")
        )
        in_progress_count = in_progress_result.scalar()
        
        # Resolved tickets
        resolved_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "resolved")
        )
        resolved_count = resolved_result.scalar()
        
        # Closed tickets
        closed_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "closed")
        )
        closed_count = closed_result.scalar()
        
        # High priority tickets
        high_priority_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.priority == "high")
        )
        high_priority_count = high_priority_result.scalar()
        
        # Urgent priority tickets
        urgent_priority_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.priority == "urgent")
        )
        urgent_priority_count = urgent_priority_result.scalar()
        
        # Today's tickets
        today = datetime.now(timezone.utc).date()
        today_result = await db.execute(
            select(func.count(Ticket.id)).where(
                func.date(Ticket.created_at) == today
            )
        )
        today_count = today_result.scalar()
        
        overview_data = {
            "total": total,
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "closed": closed_count,
            "high_priority": high_priority_count,
            "urgent_priority": urgent_priority_count,
            "today": today_count
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": overview_data,
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/overview/ticket-trend")
async def get_ticket_trend(
        days: int = 30,
        db: AsyncSession = Depends(get_async_db)
):
    """Get ticket trend data for the past N days"""
    try:
        # Get tickets created in the last N days
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await db.execute(
            select(
                func.date(Ticket.created_at).label('date'),
                func.count(Ticket.id).label('count')
            ).where(
                Ticket.created_at >= start_date
            ).group_by(
                func.date(Ticket.created_at)
            ).order_by(
                func.date(Ticket.created_at)
            )
        )
        
        trend_data = []
        for row in result:
            trend_data.append({
                "date": row.date.isoformat() if row.date else None,
                "count": row.count
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {"trend": trend_data, "days": days},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/overview/category-distribution")
async def get_category_distribution(db: AsyncSession = Depends(get_async_db)):
    """Get ticket distribution by category for pie charts"""
    try:
        # Get all categories with ticket counts
        result = await db.execute(
            select(
                TicketCategory.id,
                TicketCategory.name,
                func.count(Ticket.id).label('count')
            ).outerjoin(
                Ticket, Ticket.category_id == TicketCategory.id
            ).group_by(
                TicketCategory.id,
                TicketCategory.name
            ).order_by(
                func.count(Ticket.id).desc()
            )
        )
        
        distribution_data = []
        for row in result:
            distribution_data.append({
                "category_id": row.id,
                "category_name": row.name,
                "count": row.count
            })
        
        # Also get uncategorized tickets
        uncategorized_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.category_id.is_(None))
        )
        uncategorized_count = uncategorized_result.scalar()
        
        if uncategorized_count > 0:
            distribution_data.append({
                "category_id": None,
                "category_name": "Uncategorized",
                "count": uncategorized_count
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {"distribution": distribution_data},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/overview/status-distribution")
async def get_status_distribution(db: AsyncSession = Depends(get_async_db)):
    """Get ticket distribution by status"""
    try:
        result = await db.execute(
            select(
                Ticket.status,
                func.count(Ticket.id).label('count')
            ).group_by(
                Ticket.status
            ).order_by(
                func.count(Ticket.id).desc()
            )
        )
        
        distribution_data = []
        for row in result:
            distribution_data.append({
                "status": row.status,
                "count": row.count
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {"distribution": distribution_data},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/overview/priority-distribution")
async def get_priority_distribution(db: AsyncSession = Depends(get_async_db)):
    """Get ticket distribution by priority"""
    try:
        result = await db.execute(
            select(
                Ticket.priority,
                func.count(Ticket.id).label('count')
            ).group_by(
                Ticket.priority
            ).order_by(
                func.count(Ticket.id).desc()
            )
        )
        
        distribution_data = []
        for row in result:
            distribution_data.append({
                "priority": row.priority,
                "count": row.count
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {"distribution": distribution_data},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )
