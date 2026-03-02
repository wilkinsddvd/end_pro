from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import TicketReply, Ticket, QuickReply
from db import get_async_db
from fastapi.responses import JSONResponse
from api.deps import get_current_user_id

router = APIRouter()


@router.get("/tickets/{ticket_id}/replies")
async def list_replies(ticket_id: int, db: AsyncSession = Depends(get_async_db)):
    """获取工单的所有回复列表（按创建时间正序）"""
    try:
        stmt = (
            select(TicketReply)
            .where(TicketReply.ticket_id == ticket_id)
            .options(selectinload(TicketReply.user))
            .order_by(TicketReply.created_at.asc(), TicketReply.id.asc())
        )
        result = await db.execute(stmt)
        replies = result.scalars().all()

        reply_list = []
        for reply in replies:
            reply_list.append({
                "id": reply.id,
                "ticket_id": reply.ticket_id,
                "content": reply.content,
                "created_at": reply.created_at.strftime("%Y-%m-%d") if reply.created_at else "",
                "user": reply.user.username if reply.user else None,
                "user_id": reply.user_id,
            })

        return JSONResponse(content={
            "code": 200,
            "data": {"replies": reply_list, "total": len(reply_list)},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.post("/tickets/{ticket_id}/replies")
async def create_reply(
        ticket_id: int,
        data: dict = Body(...),
        db: AsyncSession = Depends(get_async_db),
        user_id: int = Depends(get_current_user_id)
):
    """创建回复（需要 JWT 认证）"""
    try:
        content = data.get("content")
        if not content:
            return JSONResponse(content={"code": 400, "data": {}, "msg": "content is required"})

        # 验证工单存在
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "ticket not found"})

        reply = TicketReply(
            ticket_id=ticket_id,
            user_id=user_id,
            content=content,
        )
        db.add(reply)

        # 如果传入 quick_reply_id，则递增 use_count
        quick_reply_id = data.get("quick_reply_id")
        if quick_reply_id is not None:
            qr_result = await db.execute(select(QuickReply).where(QuickReply.id == quick_reply_id))
            qr = qr_result.scalar_one_or_none()
            if qr:
                qr.use_count = (qr.use_count or 0) + 1

        await db.commit()

        return JSONResponse(content={"code": 201, "data": {}, "msg": "reply created successfully"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})


@router.delete("/tickets/{ticket_id}/replies/{reply_id}")
async def delete_reply(
        ticket_id: int,
        reply_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """删除回复"""
    try:
        stmt = select(TicketReply).where(
            TicketReply.id == reply_id,
            TicketReply.ticket_id == ticket_id
        )
        result = await db.execute(stmt)
        reply = result.scalar_one_or_none()

        if not reply:
            return JSONResponse(content={"code": 404, "data": {}, "msg": "reply not found"})

        await db.delete(reply)
        await db.commit()

        return JSONResponse(content={"code": 200, "data": {}, "msg": "reply deleted successfully"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})
