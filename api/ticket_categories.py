from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from models import TicketCategory, Ticket, User
from schemas import TicketCategoryCreate, TicketCategoryUpdate
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.dependencies import require_current_user

router = APIRouter()

@router.get("/ticket-categories")
async def get_ticket_categories(db: AsyncSession = Depends(get_async_db)):
    """Get all ticket categories with ticket counts"""
    try:
        # Optimized query using JOIN and GROUP BY to avoid N+1 queries
        result = await db.execute(
            select(
                TicketCategory.id,
                TicketCategory.name,
                TicketCategory.description,
                func.count(Ticket.id).label('count')
            ).outerjoin(
                Ticket, Ticket.category_id == TicketCategory.id
            ).group_by(
                TicketCategory.id,
                TicketCategory.name,
                TicketCategory.description
            ).order_by(
                TicketCategory.id
            )
        )
        
        cat_list = []
        for row in result:
            cat_list.append({
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "count": row.count
            })
        return JSONResponse(content={
            "code": 200,
            "data": {"categories": cat_list},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.post("/ticket-categories")
async def create_ticket_category(
    category_data: TicketCategoryCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new ticket category (requires authentication)"""
    try:
        # Check if category already exists
        result = await db.execute(select(TicketCategory).where(TicketCategory.name == category_data.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            return JSONResponse(
                status_code=409,
                content={"code": 409, "data": {}, "msg": "ticket category already exists"}
            )
        
        category = TicketCategory(
            name=category_data.name,
            description=category_data.description
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "count": 0
                },
                "msg": "ticket category created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.put("/ticket-categories/{id}")
async def update_ticket_category(
    id: int,
    category_data: TicketCategoryUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a ticket category (requires authentication)"""
    try:
        result = await db.execute(select(TicketCategory).where(TicketCategory.id == id))
        category = result.scalar_one_or_none()
        
        if not category:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "ticket category not found"}
            )
        
        # Check if new name already exists
        if category_data.name:
            name_check = await db.execute(
                select(TicketCategory).where(TicketCategory.name == category_data.name, TicketCategory.id != id)
            )
            if name_check.scalar_one_or_none():
                return JSONResponse(
                    status_code=409,
                    content={"code": 409, "data": {}, "msg": "ticket category name already exists"}
                )
            category.name = category_data.name
        
        if category_data.description is not None:
            category.description = category_data.description
        
        await db.commit()
        await db.refresh(category)
        
        count = await db.execute(select(func.count(Ticket.id)).where(Ticket.category_id == category.id))
        cnt = count.scalar()
        
        return JSONResponse(content={
            "code": 200,
            "data": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "count": cnt
            },
            "msg": "ticket category updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.delete("/ticket-categories/{id}")
async def delete_ticket_category(
    id: int,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a ticket category (requires authentication)"""
    try:
        result = await db.execute(select(TicketCategory).where(TicketCategory.id == id))
        category = result.scalar_one_or_none()
        
        if not category:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "ticket category not found"}
            )
        
        # Check if category has tickets
        count = await db.execute(select(func.count(Ticket.id)).where(Ticket.category_id == id))
        if count.scalar() > 0:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "data": {}, "msg": "ticket category has tickets, cannot delete"}
            )
        
        await db.delete(category)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "ticket category deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )
