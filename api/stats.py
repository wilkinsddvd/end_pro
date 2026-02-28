"""
Statistics endpoints for the logistics system.

Per-user stats (/api/stats/me): post count, ticket counts by status, quick reply usage.
Admin global stats (/api/stats/admin): totals and recent aggregates (admin-only).
"""
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models import Post, Ticket, QuickReply, User
from db import get_async_db
from auth_utils import get_current_user, get_current_admin
from fastapi.responses import JSONResponse
from schemas import VALID_STATUSES

router = APIRouter()


@router.get("/stats/me")
async def get_my_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Per-user statistics.
    Returns counts for posts, tickets (by status), and quick replies.
    Requires authentication.
    """
    uid = current_user.id

    # Post count
    post_count = (await db.execute(
        select(func.count()).select_from(Post).where(Post.author_id == uid)
    )).scalar() or 0

    # Ticket counts by status
    ticket_counts = {}
    for status in VALID_STATUSES:
        cnt = (await db.execute(
            select(func.count()).select_from(Ticket)
            .where(Ticket.user_id == uid, Ticket.status == status)
        )).scalar() or 0
        ticket_counts[status] = cnt

    # Quick reply count and total uses
    qr_count = (await db.execute(
        select(func.count()).select_from(QuickReply).where(QuickReply.user_id == uid)
    )).scalar() or 0

    qr_total_uses = (await db.execute(
        select(func.coalesce(func.sum(QuickReply.use_count), 0))
        .where(QuickReply.user_id == uid)
    )).scalar() or 0

    return JSONResponse(content={
        "code": 200,
        "data": {
            "post_count": post_count,
            "ticket_counts": ticket_counts,
            "quick_reply_count": qr_count,
            "quick_reply_total_uses": int(qr_total_uses),
        },
        "msg": "success"
    })


@router.get("/stats/admin")
async def get_admin_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Global admin statistics.
    Returns totals and recent (7d/30d) aggregates for all entities.
    Requires admin role.
    """
    now = datetime.date.today()
    date_7d = now - datetime.timedelta(days=7)
    date_30d = now - datetime.timedelta(days=30)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_posts = (await db.execute(select(func.count()).select_from(Post))).scalar() or 0
    total_tickets = (await db.execute(select(func.count()).select_from(Ticket))).scalar() or 0
    total_qr = (await db.execute(select(func.count()).select_from(QuickReply))).scalar() or 0

    # Tickets by status (global)
    tickets_by_status = {}
    for status in VALID_STATUSES:
        cnt = (await db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == status)
        )).scalar() or 0
        tickets_by_status[status] = cnt

    # Recent 7d
    posts_7d = (await db.execute(
        select(func.count()).select_from(Post).where(Post.date >= date_7d)
    )).scalar() or 0
    tickets_7d = (await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.created_at >= date_7d)
    )).scalar() or 0
    users_7d = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= date_7d)
    )).scalar() or 0

    # Recent 30d
    posts_30d = (await db.execute(
        select(func.count()).select_from(Post).where(Post.date >= date_30d)
    )).scalar() or 0
    tickets_30d = (await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.created_at >= date_30d)
    )).scalar() or 0
    users_30d = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= date_30d)
    )).scalar() or 0

    return JSONResponse(content={
        "code": 200,
        "data": {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_tickets": total_tickets,
            "total_quick_replies": total_qr,
            "tickets_by_status": tickets_by_status,
            "recent_7d": {
                "posts": posts_7d,
                "tickets": tickets_7d,
                "users": users_7d,
            },
            "recent_30d": {
                "posts": posts_30d,
                "tickets": tickets_30d,
                "users": users_30d,
            },
        },
        "msg": "success"
    })
