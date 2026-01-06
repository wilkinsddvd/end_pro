from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from models import Ticket, TicketCategory, User
from schemas import TicketCreate, TicketUpdate
from db import get_async_db
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from utils.dependencies import require_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.get("/tickets")
async def list_tickets(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[int] = None,
        db: AsyncSession = Depends(get_async_db)
):
    """List tickets with pagination and optional filtering"""
    try:
        # Build query with eager loading
        stmt = select(Ticket).options(
            selectinload(Ticket.category),
            selectinload(Ticket.user)
        )
        
        # Apply filters
        filters = []
        if search:
            filters.append(
                or_(
                    Ticket.title.contains(search),
                    Ticket.description.contains(search)
                )
            )
        if status:
            filters.append(Ticket.status == status)
        if priority:
            filters.append(Ticket.priority == priority)
        if category_id:
            filters.append(Ticket.category_id == category_id)
        
        if filters:
            stmt = stmt.where(*filters)
        
        # Get total count
        count_stmt = select(func.count()).select_from(Ticket)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Ticket.created_at.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        result = await db.execute(stmt)
        tickets = result.scalars().all()
        
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                "id": ticket.id,
                "title": ticket.title,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "category_id": ticket.category_id,
                "category_name": ticket.category.name if ticket.category else None,
                "user_id": ticket.user_id,
                "username": ticket.user.username if ticket.user else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {
                "page": page,
                "size": size,
                "total": total,
                "tickets": ticket_list
            },
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/tickets/{id}")
async def get_ticket(
        id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get a specific ticket by ID"""
    try:
        stmt = select(Ticket).options(
            selectinload(Ticket.category),
            selectinload(Ticket.user)
        ).where(Ticket.id == id)
        
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "ticket not found"}
            )
        
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_id": ticket.category_id,
            "category_name": ticket.category.name if ticket.category else None,
            "user_id": ticket.user_id,
            "username": ticket.user.username if ticket.user else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": ticket_data,
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.post("/tickets")
async def create_ticket(
        ticket_data: TicketCreate,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Create a new ticket (requires authentication)"""
    try:
        # Validate category if provided
        if ticket_data.category_id:
            result = await db.execute(
                select(TicketCategory).where(TicketCategory.id == ticket_data.category_id)
            )
            category = result.scalar_one_or_none()
            if not category:
                return JSONResponse(
                    status_code=404,
                    content={"code": 404, "data": {}, "msg": "category not found"}
                )
        
        ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            status=ticket_data.status or "open",
            priority=ticket_data.priority or "medium",
            category_id=ticket_data.category_id,
            user_id=current_user.id
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        # Load relationships
        stmt = select(Ticket).options(
            selectinload(Ticket.category),
            selectinload(Ticket.user)
        ).where(Ticket.id == ticket.id)
        result = await db.execute(stmt)
        ticket = result.scalar_one()
        
        ticket_data_out = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_id": ticket.category_id,
            "category_name": ticket.category.name if ticket.category else None,
            "user_id": ticket.user_id,
            "username": ticket.user.username if ticket.user else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
        }
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": ticket_data_out,
                "msg": "ticket created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.put("/tickets/{id}")
async def update_ticket(
        id: int,
        ticket_data: TicketUpdate,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Update a ticket (requires authentication)"""
    try:
        result = await db.execute(select(Ticket).where(Ticket.id == id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "ticket not found"}
            )
        
        # Validate category if provided
        if ticket_data.category_id:
            result = await db.execute(
                select(TicketCategory).where(TicketCategory.id == ticket_data.category_id)
            )
            category = result.scalar_one_or_none()
            if not category:
                return JSONResponse(
                    status_code=404,
                    content={"code": 404, "data": {}, "msg": "category not found"}
                )
        
        # Update fields
        if ticket_data.title is not None:
            ticket.title = ticket_data.title
        if ticket_data.description is not None:
            ticket.description = ticket_data.description
        if ticket_data.status is not None:
            ticket.status = ticket_data.status
        if ticket_data.priority is not None:
            ticket.priority = ticket_data.priority
        if ticket_data.category_id is not None:
            ticket.category_id = ticket_data.category_id
        
        ticket.updated_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Reload with relationships
        stmt = select(Ticket).options(
            selectinload(Ticket.category),
            selectinload(Ticket.user)
        ).where(Ticket.id == id)
        result = await db.execute(stmt)
        ticket = result.scalar_one()
        
        ticket_data_out = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_id": ticket.category_id,
            "category_name": ticket.category.name if ticket.category else None,
            "user_id": ticket.user_id,
            "username": ticket.user.username if ticket.user else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": ticket_data_out,
            "msg": "ticket updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.delete("/tickets/{id}")
async def delete_ticket(
        id: int,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Delete a ticket (requires authentication)"""
    try:
        result = await db.execute(select(Ticket).where(Ticket.id == id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "ticket not found"}
            )
        
        await db.delete(ticket)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "ticket deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )
