from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import QuickReply, User
from schemas import QuickReplyCreate, QuickReplyUpdate
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.dependencies import require_current_user

router = APIRouter()

@router.get("/quick-replies")
async def get_quick_replies(db: AsyncSession = Depends(get_async_db)):
    """Get all quick reply templates"""
    try:
        result = await db.execute(select(QuickReply).order_by(QuickReply.created_at.desc()))
        quick_replies = result.scalars().all()
        
        reply_list = []
        for reply in quick_replies:
            reply_list.append({
                "id": reply.id,
                "title": reply.title,
                "content": reply.content,
                "created_at": reply.created_at.isoformat() if reply.created_at else None,
                "updated_at": reply.updated_at.isoformat() if reply.updated_at else None
            })
        
        return JSONResponse(content={
            "code": 200,
            "data": {"quick_replies": reply_list},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.get("/quick-replies/{id}")
async def get_quick_reply(
        id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get a specific quick reply by ID"""
    try:
        result = await db.execute(select(QuickReply).where(QuickReply.id == id))
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "quick reply not found"}
            )
        
        reply_data = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "created_at": quick_reply.created_at.isoformat() if quick_reply.created_at else None,
            "updated_at": quick_reply.updated_at.isoformat() if quick_reply.updated_at else None
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": reply_data,
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.post("/quick-replies")
async def create_quick_reply(
        reply_data: QuickReplyCreate,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Create a new quick reply template (requires authentication)"""
    try:
        quick_reply = QuickReply(
            title=reply_data.title,
            content=reply_data.content
        )
        db.add(quick_reply)
        await db.commit()
        await db.refresh(quick_reply)
        
        reply_data_out = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "created_at": quick_reply.created_at.isoformat() if quick_reply.created_at else None,
            "updated_at": quick_reply.updated_at.isoformat() if quick_reply.updated_at else None
        }
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": reply_data_out,
                "msg": "quick reply created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.put("/quick-replies/{id}")
async def update_quick_reply(
        id: int,
        reply_data: QuickReplyUpdate,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Update a quick reply template (requires authentication)"""
    try:
        result = await db.execute(select(QuickReply).where(QuickReply.id == id))
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "quick reply not found"}
            )
        
        # Update fields
        if reply_data.title is not None:
            quick_reply.title = reply_data.title
        if reply_data.content is not None:
            quick_reply.content = reply_data.content
        
        await db.commit()
        await db.refresh(quick_reply)
        
        reply_data_out = {
            "id": quick_reply.id,
            "title": quick_reply.title,
            "content": quick_reply.content,
            "created_at": quick_reply.created_at.isoformat() if quick_reply.created_at else None,
            "updated_at": quick_reply.updated_at.isoformat() if quick_reply.updated_at else None
        }
        
        return JSONResponse(content={
            "code": 200,
            "data": reply_data_out,
            "msg": "quick reply updated"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )

@router.delete("/quick-replies/{id}")
async def delete_quick_reply(
        id: int,
        current_user: User = Depends(require_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """Delete a quick reply template (requires authentication)"""
    try:
        result = await db.execute(select(QuickReply).where(QuickReply.id == id))
        quick_reply = result.scalar_one_or_none()
        
        if not quick_reply:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "quick reply not found"}
            )
        
        await db.delete(quick_reply)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "quick reply deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )
